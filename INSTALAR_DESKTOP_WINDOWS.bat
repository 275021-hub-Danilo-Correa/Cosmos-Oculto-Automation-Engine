@echo off
cd /d "%~dp0"
call INSTALAR_WINDOWS.bat
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
if errorlevel 1 (
  echo A instalacao desktop falhou. Confira a mensagem acima.
  pause
  exit /b 1
)
echo Desktop instalado. Abra INICIAR_DESKTOP_WINDOWS.bat.
echo O Windows precisa do Microsoft Edge WebView2 Runtime.
pause
exit /b 0
