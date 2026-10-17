@echo off
setlocal
"%~dp0services\.venv\Scripts\python.exe" "%~dp0tools\launch_business_portal_qa.py" --page portal %*
