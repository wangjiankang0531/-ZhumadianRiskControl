@echo off
setlocal
if not exist "%~dp0Packages\active_release.json" goto legacy
set "XNBY_BOOTSTRAP=%~dp0runtime\python\python.exe"
if not exist "%XNBY_BOOTSTRAP%" set "XNBY_BOOTSTRAP=%~dp0Packages\current\runtime\python\python.exe"
"%XNBY_BOOTSTRAP%" -X utf8 "%~dp0tools\launch_selected_release.py" --state "%~dp0Packages\active_release.json" --kind scene %*
exit /b %errorlevel%
:legacy
"%~dp0Packages\current\runtime\python\python.exe" "%~dp0tools\launch_landscape_web.py" %*
