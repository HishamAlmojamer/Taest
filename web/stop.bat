@echo off
title ERP System - Stop All Services
color 0C
cls

echo ============================================
echo    ERP System - Stopping All Services
echo ============================================
echo.

echo [1/4] Stopping Frontend...
taskkill /FI "WINDOWTITLE eq ERP Frontend*" /F >NUL 2>&1
echo       Done.

echo [2/4] Stopping Gateway...
taskkill /FI "WINDOWTITLE eq ERP Gateway*" /F >NUL 2>&1
echo       Done.

echo [3/4] Stopping Backend...
taskkill /FI "WINDOWTITLE eq ERP Backend*" /F >NUL 2>&1
echo       Done.

echo [4/4] Cleaning up remaining ERP windows...
taskkill /FI "WINDOWTITLE eq ERP*" /F >NUL 2>&1
echo       Done.

echo.
echo ============================================
echo    All ERP services stopped.
echo    PostgreSQL still running (as a service).
echo ============================================
echo.
pause
