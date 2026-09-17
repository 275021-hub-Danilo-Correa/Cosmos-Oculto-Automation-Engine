@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  .venv\Scripts\python.exe iniciar.py
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    python iniciar.py
  ) else (
    py -3 iniciar.py
  )
)
if errorlevel 1 (
  echo.
  echo Instale Python 3.12 ou superior em python.org e tente novamente.
  echo Se ja estiver instalado, confira a mensagem acima.
  pause
)
