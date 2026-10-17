@echo off
setlocal
"%~dp0runtime\python\python.exe" -X utf8 "%~dp0tools\verify_native_cache.py"
