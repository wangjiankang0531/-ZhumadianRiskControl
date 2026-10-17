@echo off
setlocal
cd /d "%~dp0"
"%~dp0runtime\python\python.exe" -X utf8 "%~dp0tools\verify_native_source_family.py" %*
if errorlevel 1 exit /b 1
pause
