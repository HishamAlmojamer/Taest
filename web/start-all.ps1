# ERP System - Start All Services
# ================================
# Run this script from PowerShell: .\start-all.ps1

$ErrorActionPreference = "SilentlyContinue"
$ROOT = "C:\Users\hicom\Desktop\Taest\web"
$BACKEND_DIR = "$ROOT\backend"
$GATEWAY_DIR = "$ROOT\gateway"
$FRONTEND_DIR = "$ROOT\frontend"
$PYTHON = "$BACKEND_DIR\.venv\Scripts\python.exe"
$PSQL = "C:\Program Files\PostgreSQL\18\bin\psql.exe"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ERP System - Starting All Services" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 1. PostgreSQL
Write-Host "`n[1/4] PostgreSQL... " -ForegroundColor Yellow -NoNewline
$pgRunning = sc.exe query "postgresql*" 2>$null | Select-String "RUNNING"
if ($pgRunning) {
    Write-Host "ALREADY RUNNING" -ForegroundColor Green
} else {
    Write-Host "Starting..." -ForegroundColor Yellow
    Start-Service "postgresql*" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    $pgRunning = sc.exe query "postgresql*" 2>$null | Select-String "RUNNING"
    if ($pgRunning) { Write-Host "  STARTED" -ForegroundColor Green }
    else { Write-Host "  FAILED - Please start PostgreSQL manually" -ForegroundColor Red }
}

# Verify DB connection
$env:PGPASSWORD = "postgres"
& $PSQL -U postgres -h localhost -d warehouse_management -c "SELECT 1" -t -q 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Database connection: OK" -ForegroundColor DarkGreen
}

# 2. Backend (FastAPI)
Write-Host "[2/4] Backend (FastAPI on :8001)... " -ForegroundColor Yellow -NoNewline
$backendProc = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
if ($backendProc) {
    Write-Host "ALREADY RUNNING" -ForegroundColor Green
} else {
    Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/k", "title ERP Backend - Port 8001 && cd /d $BACKEND_DIR && `"$PYTHON`" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload" `
        -WindowStyle Normal
    Write-Host "STARTED" -ForegroundColor Green
}

# 3. Gateway (Node.js)
Write-Host "[3/4] Gateway (Node.js on :3001)... " -ForegroundColor Yellow -NoNewline
$gwProc = Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*index.ts*" -or $_.CommandLine -like "*gateway*" }
if ($gwProc) {
    Write-Host "ALREADY RUNNING" -ForegroundColor Green
} else {
    Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/k", "title ERP Gateway - Port 3001 && cd /d $GATEWAY_DIR && node node_modules\tsx\dist\cli.mjs src\index.ts" `
        -WindowStyle Normal
    Write-Host "STARTED" -ForegroundColor Green
}

# 4. Frontend (Vite)
Write-Host "[4/4] Frontend (React on :5173)... " -ForegroundColor Yellow -NoNewline
$feProc = Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*vite*" }
if ($feProc) {
    Write-Host "ALREADY RUNNING" -ForegroundColor Green
} else {
    Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/k", "title ERP Frontend - Port 5173 && cd /d $FRONTEND_DIR && npm run dev" `
        -WindowStyle Normal
    Write-Host "STARTED" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Waiting for services to initialize..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green

Start-Sleep -Seconds 8

Write-Host "`nService Status:" -ForegroundColor White

# Check Backend
try {
    $backendHealth = Invoke-RestMethod -Uri "http://localhost:8001/api/health" -Method GET -TimeoutSec 3
    Write-Host "  [OK] Backend  : http://localhost:8001" -ForegroundColor Green
    Write-Host "         Docs   : http://localhost:8001/docs" -ForegroundColor DarkGray
} catch {
    Write-Host "  [..] Backend  : Starting... check 'ERP Backend' window" -ForegroundColor Yellow
}

# Check Gateway
try {
    $gwHealth = Invoke-RestMethod -Uri "http://localhost:3001/health" -Method GET -TimeoutSec 3
    Write-Host "  [OK] Gateway  : http://localhost:3001" -ForegroundColor Green
} catch {
    Write-Host "  [..] Gateway  : Starting... check 'ERP Gateway' window" -ForegroundColor Yellow
}

# Check Frontend
try {
    $feHealth = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 3
    Write-Host "  [OK] Frontend : http://localhost:5173" -ForegroundColor Green
} catch {
    Write-Host "  [..] Frontend : Starting... check 'ERP Frontend' window" -ForegroundColor Yellow
}

Write-Host "  [OK] Database : PostgreSQL on localhost:5432" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Access URLs:" -ForegroundColor White
Write-Host "    Frontend  : http://localhost:5173" -ForegroundColor Cyan
Write-Host "    Backend   : http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "    Gateway   : http://localhost:3001" -ForegroundColor Cyan
Write-Host "    Database  : localhost:5432" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host "  To stop: run .\stop-all.ps1" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
