@echo off
setlocal
cd /d "%~dp0"

echo Press Ctrl+C in this window to stop the bridge.
echo.

python -u keyboard_bridge.py

if errorlevel 1 pause
endlocal
