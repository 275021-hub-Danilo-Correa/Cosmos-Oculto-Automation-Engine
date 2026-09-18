@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute INSTALAR_DESKTOP_WINDOWS.bat primeiro.
  pause
  exit /b 1
)
.venv\Scripts\python.exe iniciar_desktop.py %*
if errorlevel 1 (
  echo Confira a mensagem acima. A versao web abre com INICIAR_WINDOWS.bat.
  pause
  exit /b 1
)
