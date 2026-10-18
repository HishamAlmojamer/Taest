@echo off
title ERP System - Service Status
color 0B
cls

echo ============================================
echo    ERP System - Service Status
echo ============================================
echo.

REM Check PostgreSQL
echo [1/4] PostgreSQL...
sc query "postgresql*" 2>NUL | find "RUNNING" >NUL
if %ERRORLEVEL% == 0 (
    echo       [OK] Running on port 5432
) else (
    echo       [!!] NOT RUNNING
)

REM Check Backend
echo [2/4] Backend (FastAPI)...
curl -s http://localhost:8001/api/health >NUL 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Running on port 8001
    echo            Docs: http://localhost:8001/docs
) else (
    echo       [!!] NOT RUNNING
)

REM Check Gateway
echo [3/4] Gateway (Node.js)...
curl -s http://localhost:3001/health >NUL 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Running on port 3001
) else (
    echo       [!!] NOT RUNNING
)

REM Check Frontend
echo [4/4] Frontend (React)...
curl -s http://localhost:5173 >NUL 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Running on port 5173
    echo            URL: http://localhost:5173
) else (
    echo       [!!] NOT RUNNING
)

echo.
echo ============================================
echo    Quick Links:
echo    Frontend  : http://localhost:5173
echo    Backend   : http://localhost:8001/docs
echo    Gateway   : http://localhost:3001
echo ============================================
echo.
pause
