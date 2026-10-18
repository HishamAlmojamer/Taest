# ERP System - Stop All Services
# ================================
# Run this script from PowerShell: .\stop-all.ps1

Write-Host "========================================" -ForegroundColor Red
Write-Host "  ERP System - Stopping All Services" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red

# Stop Frontend
Write-Host "`n[1/4] Stopping Frontend..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*vite*" } | Stop-Process -Force -ErrorAction SilentlyContinue
taskkill /FI "WINDOWTITLE eq ERP Frontend*" /F 2>$null | Out-Null
Write-Host "  Done" -ForegroundColor Green

# Stop Gateway
Write-Host "[2/4] Stopping Gateway..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*index.ts*" } | Stop-Process -Force -ErrorAction SilentlyContinue
taskkill /FI "WINDOWTITLE eq ERP Gateway*" /F 2>$null | Out-Null
Write-Host "  Done" -ForegroundColor Green

# Stop Backend
Write-Host "[3/4] Stopping Backend..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
taskkill /FI "WINDOWTITLE eq ERP Backend*" /F 2>$null | Out-Null
Write-Host "  Done" -ForegroundColor Green

# Clean up any remaining ERP windows
Write-Host "[4/4] Cleaning up..." -ForegroundColor Yellow
taskkill /FI "WINDOWTITLE eq ERP*" /F 2>$null | Out-Null
Write-Host "  Done" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  All ERP services stopped." -ForegroundColor Green
Write-Host "  PostgreSQL is still running as a service." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
