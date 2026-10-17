@echo off
setlocal
cd /d "%~dp0"
if not exist "services\.venv\Scripts\python.exe" (
  echo API Python environment missing. See services\README.md.
  pause
  exit /b 2
)
"services\.venv\Scripts\python.exe" tools\probe_business_api.py
set "probe_result=%errorlevel%"
if not "%~1"=="--no-pause" pause
exit /b %probe_result%
