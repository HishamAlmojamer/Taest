@echo off
chcp 65001 >nul
title HM Next ERP - Stop
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0erp.ps1" -Action stop
echo.
pause
