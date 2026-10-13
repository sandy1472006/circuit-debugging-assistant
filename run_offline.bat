@echo off
title Circuit Debugging Assistant - Offline Mode
cd /d "%~dp0"

echo ======================================================================
echo    CIRCUIT DEBUGGING ASSISTANT (CDA) - OFFLINE RUNNER
echo    KK Wagh College of Engineering, Nashik
echo ======================================================================
echo.
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH!
    echo Please install Python 3.10+ and make sure to check "Add Python to PATH".
    pause
    exit /b 1
)

echo [2/3] Opening browser at http://localhost:8000 ...
start "" timeout /t 2 /nobreak >nul & start "" http://localhost:8000

echo [3/3] Starting local diagnostic engine (Port 8000)...
echo.
echo ======================================================================
echo  Server is running locally without internet!
echo  - Open on this laptop:   http://localhost:8000
echo  - Press Ctrl+C in this window to stop the server.
echo ======================================================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
