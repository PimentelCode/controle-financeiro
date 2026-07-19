@echo off
REM Reconstroi o FinanControl.exe apos editar FinanControl.html ou server.py
cd /d "%~dp0"
echo Construindo FinanControl.exe...
pyinstaller --onefile --name FinanControl ^
  --add-data "%~dp0FinanControl.html;." ^
  --distpath dist --workpath build_tmp --specpath build_tmp ^
  "%~dp0server.py"
echo.
echo Pronto. Executavel em: dist\FinanControl.exe
pause
