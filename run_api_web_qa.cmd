@echo off
setlocal
cd /d "%~dp0"
if not exist "services\.venv\Scripts\python.exe" (
 echo API environment missing. See services\README.md.
 pause
 exit /b 2
)
"services\.venv\Scripts\python.exe" tools\launch_business_portal_qa.py %*
exit /b %errorlevel%
