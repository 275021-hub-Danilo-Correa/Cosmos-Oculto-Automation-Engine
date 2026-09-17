@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python -c "import sys; sys.exit(sys.version_info < (3,12))"
  if errorlevel 1 goto python_error
  python -m venv .venv
) else (
  py -3 -c "import sys; sys.exit(sys.version_info < (3,12))"
  if errorlevel 1 goto python_error
  py -3 -m venv .venv
)
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements-audio.txt -r requirements-images.txt -r requirements-api.txt
if errorlevel 1 goto error
echo Instalacao concluida. Abra INICIAR_WINDOWS.bat.
echo MP3/M4A precisam tambem de FFmpeg/FFprobe no PATH.
pause
exit /b 0
:python_error
echo Instale Python 3.12 ou superior, marcando Add Python to PATH.
:error
echo A instalacao nao terminou. Confira a mensagem acima.
pause
exit /b 1
