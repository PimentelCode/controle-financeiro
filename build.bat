@echo off
REM Reconstroi o FinanControl.exe apos editar FinanControl.html ou server.py
cd /d "%~dp0"
echo Construindo FinanControl.exe...
pyinstaller --onefile --name FinanControl --icon "%~dp0FinanControl.ico" ^
  --add-data "%~dp0FinanControl.html;." ^
  --add-data "%~dp0FinanControl.ico;." ^
  --distpath dist --workpath build_tmp --specpath build_tmp ^
  "%~dp0server.py"
echo.
echo Pronto. Executavel em: dist\FinanControl.exe
pause
