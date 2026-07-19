# -*- coding: utf-8 -*-
"""
FinanControl — servidor local + backup em disco.
Roda como app desktop: abre o navegador em http://localhost e grava
os backups na mesma pasta do executavel (sobrescreve o principal,
mantem 7 snapshots diarios, poda o resto).
"""
import sys, os, re, json, threading, webbrowser, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.stdout.reconfigure(encoding="utf-8")

PORT = 8756
MAIN_FILE = "financontrol-backup.json"
KEEP_SNAPSHOTS = 7
SNAP_RE = re.compile(r"^financontrol-\d{4}-\d{2}-\d{2}\.json$")


def base_dir():
    """Pasta onde ficam os backups (ao lado do exe/script)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir():
    """Pasta com os recursos embutidos (HTML)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def read_html():
    path = os.path.join(bundle_dir(), "FinanControl.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def today_iso():
    import datetime
    return datetime.date.today().isoformat()


def write_backup(state_json):
    d = base_dir()
    # arquivo principal — sempre sobrescrito
    with open(os.path.join(d, MAIN_FILE), "w", encoding="utf-8") as f:
        f.write(state_json)
    # snapshot diario
    snap = os.path.join(d, f"financontrol-{today_iso()}.json")
    with open(snap, "w", encoding="utf-8") as f:
        f.write(state_json)
    prune_snapshots(d)


def prune_snapshots(d):
    snaps = sorted(n for n in os.listdir(d) if SNAP_RE.match(n))
    for old in snaps[:-KEEP_SNAPSHOTS]:
        try:
            os.remove(os.path.join(d, old))
        except OSError:
            pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silencia log no console

    def _send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html", "/FinanControl.html"):
            self._send(200, read_html(), "text/html")
        elif self.path == "/favicon.ico":
            ico = os.path.join(bundle_dir(), "FinanControl.ico")
            if os.path.exists(ico):
                with open(ico, "rb") as f:
                    self._send(200, f.read(), "image/x-icon")
            else:
                self._send(404, b"", "image/x-icon")
        elif self.path == "/api/ping":
            self._send(200, json.dumps({"ok": True, "app": "financontrol"}))
        elif self.path == "/api/backup":
            path = os.path.join(base_dir(), MAIN_FILE)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    self._send(200, f.read())
            else:
                self._send(200, "null")
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path == "/api/backup":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length).decode("utf-8")
                json.loads(raw)  # valida
                write_backup(raw)
                self._send(200, json.dumps({"ok": True, "file": MAIN_FILE}))
            except Exception as e:
                self._send(400, json.dumps({"ok": False, "error": str(e)}))
        else:
            self._send(404, json.dumps({"error": "not found"}))


def find_browser():
    """Acha Chrome ou Edge para abrir em modo app (janela isolada)."""
    env = os.environ
    candidates = [
        os.path.join(env.get("PROGRAMFILES", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(env.get("PROGRAMFILES(X86)", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(env.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(env.get("PROGRAMFILES(X86)", ""), r"Microsoft\Edge\Application\msedge.exe"),
        os.path.join(env.get("PROGRAMFILES", ""), r"Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def open_app(url):
    """Abre em modo aplicativo (--app) se possivel; senao, aba normal."""
    browser = find_browser()
    if browser:
        profile = os.path.join(base_dir(), ".appwindow")  # janela/estado isolado
        try:
            subprocess.Popen([
                browser,
                f"--app={url}",
                f"--user-data-dir={profile}",
                "--new-window",
                "--window-size=1200,860",
            ])
            return
        except Exception:
            pass
    webbrowser.open(url)


def main():
    url = f"http://localhost:{PORT}/"
    print("=" * 46)
    print("  FinanControl rodando")
    print(f"  Abra no navegador: {url}")
    print(f"  Backups salvos em: {base_dir()}")
    print("  Feche esta janela para encerrar o app.")
    print("=" * 46)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"Porta {PORT} ocupada — o app ja esta aberto? Abrindo navegador.")
        open_app(url)
        return
    threading.Timer(0.8, lambda: open_app(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")


if __name__ == "__main__":
    main()
