@echo off
echo ╔══════════════════════════════════════════════════════════╗
echo ║     HR SCREENING SYSTEM - LOAD TEST LAUNCHER            ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

echo Checking if backend is running...
curl -s http://127.0.0.1:8000/api/v1/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend is not running!
    echo.
    echo Please start the backend first:
    echo    python -m uvicorn app.main:app --reload --port 8000
    echo.
    pause
    exit /b 1
)

echo ✅ Backend is running
echo.
echo Select load test type:
echo.
echo 1. Simple Load Test (Quick - Python script)
echo 2. Advanced Load Test (Locust Web UI)
echo 3. Stress Test (High load)
echo 4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running simple load test...
    python load_test.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo Starting Locust web UI...
    echo Open http://localhost:8089 in your browser
    echo.
    locust -f locustfile.py --host=http://127.0.0.1:8000
) else if "%choice%"=="3" (
    echo.
    echo Running stress test (50 users, 5 min)...
    locust -f locustfile.py --host=http://127.0.0.1:8000 --users 50 --spawn-rate 5 --run-time 5m --headless
    pause
) else if "%choice%"=="4" (
    exit /b 0
) else (
    echo Invalid choice!
    pause
)
