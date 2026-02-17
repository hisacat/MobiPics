@echo off

REM Check if dependencies are installed
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

python src/main.py

pause
