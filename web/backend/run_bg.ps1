$env:DEBUG = "true"
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/warehouse_management"
# JWT_SECRET comes from backend/.env (or the process environment).
$env:CACHE_ENABLED = "false"
$env:PYTHONUNBUFFERED = "1"
Set-Location $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\python.exe" -u -m uvicorn app.main:app --host 0.0.0.0 --port 8001 *>&1 |
    ForEach-Object { "{0} {1}" -f (Get-Date -Format "HH:mm:ss"), $_ } |
    Tee-Object -FilePath "$PSScriptRoot\uvicorn_run.log"
Read-Host "uvicorn exited - press Enter to close"
