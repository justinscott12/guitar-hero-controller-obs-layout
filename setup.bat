@echo off
setlocal
cd /d "%~dp0"

if not exist "requirements.txt" (
    echo requirements.txt not found.
    exit /b 1
)

echo Installing dependencies from requirements.txt ...
pip install -r requirements.txt
if errorlevel 1 (
    echo pip install failed.
    exit /b 1
)

echo.
echo Setup complete. Run start.bat to start the keyboard bridge.
endlocal
