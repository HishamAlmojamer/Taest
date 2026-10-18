@echo off
title ERP System - Startup
color 0A
cls

echo ============================================
echo    ERP System - Starting All Services
echo ============================================
echo.

set "ROOT=C:\Users\hicom\Desktop\Taest\web"
set "BACKEND_DIR=%ROOT%\backend"
set "GATEWAY_DIR=%ROOT%\gateway"
set "FRONTEND_DIR=%ROOT%\frontend"
set "PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"
set "PSQL=C:\Program Files\PostgreSQL\18\bin\psql.exe"
set "PGPASS=postgres"

REM ============================================
REM 1. Start PostgreSQL
REM ============================================
echo [1/4] Checking PostgreSQL...
tasklist /FI "IMAGENAME eq postgres.exe" 2>NUL | find /I "postgres.exe" >NUL
if %ERRORLEVEL% == 0 (
    echo       [OK] PostgreSQL already running
) else (
    echo       Starting PostgreSQL...
    sc start "postgresql*" >NUL 2>&1
    timeout /t 3 /nobreak >NUL
    tasklist /FI "IMAGENAME eq postgres.exe" 2>NUL | find /I "postgres.exe" >NUL
    if %ERRORLEVEL% == 0 (
        echo       [OK] PostgreSQL started
    ) else (
        echo       [!!] PostgreSQL failed to start. Please start it manually.
    )
)

REM Verify DB connection
set PGPASSWORD=%PGPASS%
"%PSQL%" -U postgres -h localhost -d warehouse_management -c "SELECT 1" -t -q >NUL 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Database connection verified
) else (
    echo       [!!] Database connection failed
)

REM ============================================
REM 2. Start Backend (FastAPI)
REM ============================================
echo [2/4] Starting Backend (FastAPI on :8001)...
tasklist /FI "WINDOWTITLE eq ERP Backend*" 2>NUL | find /I "cmd.exe" >NUL
if %ERRORLEVEL% == 0 (
    echo       [OK] Backend already running
) else (
    start "ERP Backend - Port 8001" cmd /k "title ERP Backend - Port 8001 && cd /d %BACKEND_DIR% && %PYTHON% -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
    echo       [OK] Backend starting...
)

REM ============================================
REM 3. Start Gateway (Node.js)
REM ============================================
echo [3/4] Starting Gateway (Node.js on :3001)...
tasklist /FI "WINDOWTITLE eq ERP Gateway*" 2>NUL | find /I "cmd.exe" >NUL
if %ERRORLEVEL% == 0 (
    echo       [OK] Gateway already running
) else (
    start "ERP Gateway - Port 3001" cmd /k "title ERP Gateway - Port 3001 && cd /d %GATEWAY_DIR% && node node_modules\tsx\dist\cli.mjs src\index.ts"
    echo       [OK] Gateway starting...
)

REM ============================================
REM 4. Start Frontend (Vite)
REM ============================================
echo [4/4] Starting Frontend (React on :5173)...
tasklist /FI "WINDOWTITLE eq ERP Frontend*" 2>NUL | find /I "cmd.exe" >NUL
if %ERRORLEVEL% == 0 (
    echo       [OK] Frontend already running
) else (
    start "ERP Frontend - Port 5173" cmd /k "title ERP Frontend - Port 5173 && cd /d %FRONTEND_DIR% && npm run dev"
    echo       [OK] Frontend starting...
)

REM ============================================
REM Wait and check
REM ============================================
echo.
echo ============================================
echo    Waiting for services to start...
echo ============================================
timeout /t 8 /nobreak >NUL

echo.
echo Checking services...
echo.

REM Check Backend
curl -s http://localhost:8001/api/health >NUL 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Backend  : http://localhost:8001
    echo            Docs : http://localhost:8001/docs
) else (
    echo [..] Backend  : Starting... check "ERP Backend" window
)

REM Check Gateway
curl -s http://localhost:3001/health >NUL 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Gateway  : http://localhost:3001
) else (
    echo [..] Gateway  : Starting... check "ERP Gateway" window
)

REM Check Frontend
curl -s http://localhost:5173 >NUL 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Frontend : http://localhost:5173
) else (
    echo [..] Frontend : Starting... check "ERP Frontend" window
)

echo.
echo [OK] Database : PostgreSQL on localhost:5432
echo.
echo ============================================
echo    All URLs:
echo    ----------------------------------------
echo    Frontend  : http://localhost:5173
echo    Backend   : http://localhost:8001/docs
echo    Gateway   : http://localhost:3001
echo    Database  : localhost:5432
echo ============================================
echo.
echo To stop all services, run: stop.bat
echo.
pause
