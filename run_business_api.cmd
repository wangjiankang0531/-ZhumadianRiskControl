@echo off
setlocal
cd /d "%~dp0"
if not exist "services\.venv\Scripts\python.exe" (
  echo API Python environment missing. See services\README.md.
  exit /b 2
)
"services\.venv\Scripts\python.exe" -m services.api --config "..\Assets\Configuration\api.json" %*
exit /b %errorlevel%
