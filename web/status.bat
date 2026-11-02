@echo off
chcp 65001 >nul
title HM Next ERP - Status
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0erp.ps1" -Action status
echo.
pause
