@echo off
title ERP Gateway - Port 3001
cd /d "%~dp0gateway"
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/warehouse_management
set PYTHON_BACKEND_URL=http://localhost:8001
set CORS_ORIGINS=http://localhost:5173,http://localhost:3001
node node_modules\tsx\dist\cli.mjs src\index.ts
pause
