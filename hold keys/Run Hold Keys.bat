@echo off
py "%~dp0hold_keys.py"
if errorlevel 1 python "%~dp0hold_keys.py"
pause
