@echo off
REM HR Screening System - Docker Deployment Script
REM Quick deployment for Windows

echo.
echo ========================================
echo   HR Screening System - Deployment
echo ========================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Please edit .env file and add your UltraSafe API key
    echo Opening .env file...
    notepad .env
    echo.
    echo Press any key after saving your API key...
    pause >nul
)

echo [OK] Environment file exists
echo.

REM Ask user what to do
echo What would you like to do?
echo.
echo 1. Build and start (first time deployment)
echo 2. Start existing containers
echo 3. Stop containers
echo 4. Restart containers
echo 5. View logs
echo 6. Clean everything and rebuild
echo 7. Exit
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto build_start
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto restart
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto clean_rebuild
if "%choice%"=="7" goto end

echo Invalid choice!
pause
exit /b 1

:build_start
echo.
echo [STEP 1/3] Building Docker images...
echo This may take 5-10 minutes on first run...
echo.
docker-compose build
if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [STEP 2/3] Starting containers...
echo.
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start containers!
    pause
    exit /b 1
)

echo.
echo [STEP 3/3] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo [SUCCESS] Deployment complete!
echo.
goto show_urls

:start
echo.
echo Starting containers...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start containers!
    pause
    exit /b 1
)
echo [SUCCESS] Containers started!
goto show_urls

:stop
echo.
echo Stopping containers...
docker-compose stop
echo [SUCCESS] Containers stopped!
goto end

:restart
echo.
echo Restarting containers...
docker-compose restart
echo [SUCCESS] Containers restarted!
goto show_urls

:logs
echo.
echo Showing logs (Press Ctrl+C to exit)...
echo.
docker-compose logs -f
goto end

:clean_rebuild
echo.
echo [WARNING] This will remove all containers, images, and data!
set /p confirm="Are you sure? (yes/no): "
if not "%confirm%"=="yes" (
    echo Cancelled.
    goto end
)

echo.
echo Cleaning up...
docker-compose down -v --rmi all
echo.
echo Rebuilding...
docker-compose build --no-cache
echo.
echo Starting...
docker-compose up -d
echo.
echo [SUCCESS] Clean rebuild complete!
goto show_urls

:show_urls
echo.
echo ========================================
echo   Application URLs
echo ========================================
echo.
echo Frontend:  http://localhost
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo Health:    http://localhost:8000/api/v1/health
echo.
echo ========================================
echo.

REM Check health
echo Checking API health...
timeout /t 3 /nobreak >nul
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] API not responding yet. It may still be starting up.
    echo Check logs with: docker-compose logs -f
) else (
    echo [OK] API is healthy!
)

echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
echo.

REM Ask if user wants to open browser
set /p open="Open application in browser? (y/n): "
if /i "%open%"=="y" (
    start http://localhost
    start http://localhost:8000/docs
)

:end
echo.
echo Press any key to exit...
pause >nul
