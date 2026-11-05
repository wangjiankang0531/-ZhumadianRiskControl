@echo off
"C:\inetpub\wwwroot\Zhumadian\Application\runtime\python\python.exe" -I -B "%~dp0deploy_event_write_results_r48.py"
set "xnby_r48r3_exit=%errorlevel%"
echo R48_R3_COMMAND_FINISHED_EXIT_CODE=%xnby_r48r3_exit%
pause
exit /b %xnby_r48r3_exit%
