#requires -Version 5.1
<#
  HM Next ERP - Unified Launcher
  ==============================
  Starts / stops / reports the full stack:
    1) PostgreSQL  (:5432)  - Windows service
    2) FastAPI     (:8001)  - backend\app
    3) Gateway     (:3001)  - gateway\src
    4) Frontend    (:5173)  - frontend (Vite)

  Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File .\web\erp.ps1 -Action start
    powershell -NoProfile -ExecutionPolicy Bypass -File .\web\erp.ps1 -Action stop
    powershell -NoProfile -ExecutionPolicy Bypass -File .\web\erp.ps1 -Action restart
    powershell -NoProfile -ExecutionPolicy Bypass -File .\web\erp.ps1 -Action status

  Options:
    -Dev        enable hot-reload (uvicorn --reload + tsx watch)
    -NoBrowser  do not open the browser after a successful start
#>
[CmdletBinding()]
param(
    [ValidateSet('start','stop','restart','status')]
    [string]$Action = 'start',
    [switch]$Dev,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# ------------------------------------------------------------------ paths
$WEB          = $PSScriptRoot
$BACKEND_DIR  = Join-Path $WEB 'backend'
$GATEWAY_DIR  = Join-Path $WEB 'gateway'
$FRONTEND_DIR = Join-Path $WEB 'frontend'
$LOG_DIR      = Join-Path $WEB 'logs'

$PYTHON       = Join-Path $BACKEND_DIR '.venv\Scripts\python.exe'
$TSX_ENTRY    = Join-Path $GATEWAY_DIR 'node_modules\tsx\dist\cli.mjs'
$VITE_ENTRY   = Join-Path $FRONTEND_DIR 'node_modules\vite\bin\vite.js'

$P_BACKEND = 8001
$P_GATEWAY = 3001
$P_FRONT   = 5173
$P_DB      = 5432

$URL_BACKEND = "http://127.0.0.1:$P_BACKEND/api/health"
$URL_GATEWAY = "http://127.0.0.1:$P_GATEWAY/health"
# Vite binds to `localhost` (IPv6 ::1), not to 127.0.0.1
$URL_FRONT   = "http://localhost:$P_FRONT/"

# ---------------------------------------------------------------- helpers
function Write-Ok   { param([string]$Text) Write-Host "  [OK] $Text" -ForegroundColor Green }
function Write-Note { param([string]$Text) Write-Host "  [..] $Text" -ForegroundColor Yellow }
function Write-Fail { param([string]$Text) Write-Host "  [XX] $Text" -ForegroundColor Red }
function Write-Section { param([string]$Text) Write-Host ''; Write-Host $Text -ForegroundColor Cyan }

function Test-Port {
    param([int]$Port)
    $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
         Select-Object -First 1
    return [bool]$c
}

function Get-PortPids {
    param([int]$Port)
    return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
             Select-Object -ExpandProperty OwningProcess -Unique |
             Where-Object { $_ })
}

function Wait-Url {
    param([string]$Url, [int]$TimeoutSec = 90)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { return $true }
        } catch { }
        Start-Sleep -Milliseconds 700
    }
    return $false
}

function Get-EnvValue {
    param([string]$Path, [string]$Key, [string]$Default)
    if (Test-Path -LiteralPath $Path) {
        $pattern = '^\s*' + [regex]::Escape($Key) + '\s*='
        $line = Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue |
                Where-Object { $_ -match $pattern } |
                Select-Object -First 1
        if ($line) { return (($line -split '=', 2)[1]).Trim() }
    }
    return $Default
}

function Quote-Arg {
    param([string]$Value)
    if ($Value -match '\s') { return '"' + $Value + '"' }
    return $Value
}

function Resolve-Node {
    $c = Get-Command node -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $fallback = Join-Path $env:ProgramFiles 'nodejs\node.exe'
    if (Test-Path -LiteralPath $fallback) { return $fallback }
    return $null
}

function Resolve-Psql {
    $list = @()
    if ($env:ProgramFiles) {
        $list += Get-ChildItem (Join-Path $env:ProgramFiles 'PostgreSQL\*\bin\psql.exe') -ErrorAction SilentlyContinue
    }
    if (${env:ProgramFiles(x86)}) {
        $list += Get-ChildItem (Join-Path ${env:ProgramFiles(x86)} 'PostgreSQL\*\bin\psql.exe') -ErrorAction SilentlyContinue
    }
    if ($list.Count -gt 0) {
        return ($list | Sort-Object FullName -Descending | Select-Object -First 1).FullName
    }
    $cmd = Get-Command psql.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Test-Database {
    $psql = Resolve-Psql
    if (-not $psql) { return $null }
    $env:PGPASSWORD = Get-EnvValue (Join-Path $BACKEND_DIR '.env') 'PGPASSWORD' 'postgres'
    $env:PGCLIENTENCODING = 'UTF8'
    & $psql -U postgres -h 127.0.0.1 -p $P_DB -d warehouse_management -c 'SELECT 1' -t -q 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Start-Postgres {
    if (Test-Port $P_DB) { Write-Ok 'PostgreSQL يعمل بالفعل'; return $true }
    $svc = Get-Service -ErrorAction SilentlyContinue |
           Where-Object { $_.Name -like 'postgresql*' -or $_.DisplayName -like '*PostgreSQL*' } |
           Select-Object -First 1
    if (-not $svc) {
        Write-Fail 'لم يتم العثور على خدمة PostgreSQL على هذا الجهاز'
        return $false
    }
    Write-Note "تشغيل خدمة $($svc.Name) ..."
    try {
        Start-Service -Name $svc.Name -ErrorAction Stop
    } catch {
        Write-Fail "تعذّر تشغيل الخدمة: $($_.Exception.Message)"
        Write-Note 'إن كانت الخدمة متوقفة، شغّل هذا الملف كمسؤول (Run as administrator).'
        return $false
    }
    for ($i = 0; $i -lt 20; $i++) {
        if (Test-Port $P_DB) { Write-Ok 'PostgreSQL جاهز'; return $true }
        Start-Sleep -Seconds 1
    }
    Write-Fail 'PostgreSQL لم يبدأ خلال المهلة'
    return $false
}

function Start-Bg {
    param(
        [string]$Name,
        [string]$WorkDir,
        [string]$FilePath,
        [string]$ArgLine
    )
    $out = Join-Path $LOG_DIR "$Name.log"
    $err = Join-Path $LOG_DIR "$Name.err.log"
    Set-Content -LiteralPath $out -Value '' -Encoding ASCII
    Set-Content -LiteralPath $err -Value '' -Encoding ASCII
    $p = Start-Process -FilePath $FilePath `
                       -ArgumentList $ArgLine `
                       -WorkingDirectory $WorkDir `
                       -RedirectStandardOutput $out `
                       -RedirectStandardError $err `
                       -WindowStyle Hidden `
                       -PassThru
    Set-Content -LiteralPath (Join-Path $LOG_DIR "$Name.pid") -Value $p.Id -Encoding ASCII
    return $p
}

function Show-LogTail {
    param([string]$Name, [int]$Lines = 25)
    foreach ($suffix in @('.err.log', '.log')) {
        $f = Join-Path $LOG_DIR ($Name + $suffix)
        if (Test-Path -LiteralPath $f) {
            $tail = Get-Content -LiteralPath $f -Tail $Lines -ErrorAction SilentlyContinue
            if ($tail) {
                Write-Host "  --- $Name$suffix ---" -ForegroundColor DarkGray
                $tail | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
            }
        }
    }
}

function Stop-AllServices {
    Write-Section 'إيقاف خدمات النظام'
    $targets = @(
        @{ Name = 'frontend'; Port = $P_FRONT },
        @{ Name = 'gateway';  Port = $P_GATEWAY },
        @{ Name = 'backend';  Port = $P_BACKEND }
    )
    foreach ($t in $targets) {
        $name = $t.Name
        $port = [int]$t.Port
        $did = $false

        $pidFile = Join-Path $LOG_DIR "$name.pid"
        if (Test-Path -LiteralPath $pidFile) {
            $saved = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($saved) {
                taskkill /PID $saved /T /F 2>$null | Out-Null
                $did = $true
            }
            Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
        }

        foreach ($procId in (Get-PortPids $port)) {
            taskkill /PID $procId /T /F 2>$null | Out-Null
            $did = $true
        }

        if ($did) { Write-Ok "$name متوقف" } else { Write-Note "$name لم يكن يعمل" }
    }

    # Windows created by the legacy scripts
    foreach ($title in @('ERP Frontend*','ERP Gateway*','ERP Backend*','ERP*')) {
        taskkill /FI "WINDOWTITLE eq $title" /F 2>$null | Out-Null
    }
}

function Show-Status {
    Write-Host ''
    Write-Host '========================================' -ForegroundColor Green
    Write-Host '   HM Next ERP - حالة الخدمات' -ForegroundColor Green
    Write-Host '========================================' -ForegroundColor Green
    Start-Sleep -Milliseconds 150

    $rows = @(
        @{ Name = 'PostgreSQL'; Port = $P_DB;      Url = $null },
        @{ Name = 'Backend';    Port = $P_BACKEND; Url = $URL_BACKEND },
        @{ Name = 'Gateway';    Port = $P_GATEWAY; Url = $URL_GATEWAY },
        @{ Name = 'Frontend';   Port = $P_FRONT;   Url = $URL_FRONT }
    )
    foreach ($r in $rows) {
        $up = Test-Port $r.Port
        if ($up -and $r.Url) {
            try { Invoke-WebRequest -Uri $r.Url -UseBasicParsing -TimeoutSec 4 | Out-Null }
            catch { $up = $false }
        }
        $label = '{0,-12} :{1}' -f $r.Name, $r.Port
        if ($up) { Write-Ok $label } else { Write-Fail "$label (متوقف)" }
    }
    Write-Host ''
}

function Invoke-Start {
    Write-Host ''
    Write-Host '========================================' -ForegroundColor Green
    Write-Host '   HM Next ERP - تشغيل النظام' -ForegroundColor Green
    Write-Host '========================================' -ForegroundColor Green

    # ----- prerequisites
    if (-not (Test-Path -LiteralPath $PYTHON)) {
        Write-Fail "لم يتم العثور على Python venv: $PYTHON"
        Write-Note 'أنشئ البيئة: python -m venv backend\.venv ثم backend\.venv\Scripts\pip install -e backend'
        return $false
    }
    if (-not (Test-Path -LiteralPath $TSX_ENTRY)) {
        Write-Fail 'حزم gateway غير مثبتة (node_modules)'
        Write-Note 'شغّل: cd web\gateway ; npm install'
        return $false
    }
    if (-not (Test-Path -LiteralPath $VITE_ENTRY)) {
        Write-Fail 'حزم frontend غير مثبتة (node_modules)'
        Write-Note 'شغّل: cd web\frontend ; npm install'
        return $false
    }
    $NODE = Resolve-Node
    if (-not $NODE) {
        Write-Fail 'Node.js غير مثبت أو غير موجود على PATH'
        return $false
    }

    New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

    # ----- 1) PostgreSQL
    Write-Section '[1/4] قاعدة البيانات (PostgreSQL :5432)'
    if (-not (Start-Postgres)) { return $false }
    $db = Test-Database
    if ($db -eq $true) {
        Write-Ok 'الاتصال بقاعدة warehouse_management ناجح'
    } elseif ($db -eq $false) {
        Write-Fail 'تعذّر الاتصال بقاعدة warehouse_management'
        Write-Note 'تحقّق من المستخدم/كلمة المرور في web\backend\.env'
        return $false
    } else {
        Write-Note 'psql غير متاح - تم تخطي التحقق العميق من قاعدة البيانات'
    }

    # ----- shared environment (each service also reads its own .env)
    $env:JWT_SECRET      = Get-EnvValue (Join-Path $BACKEND_DIR '.env') 'JWT_SECRET' ''
    $env:CACHE_ENABLED   = 'false'
    $env:PYTHONUNBUFFERED = '1'
    $env:NO_COLOR        = '1'

    # ----- 2) Backend
    Write-Section '[2/4] الخادم الخلفي (FastAPI :8001)'
    if (Test-Port $P_BACKEND) {
        Write-Ok 'يعمل بالفعل - تم تخطي التشغيل'
    } else {
        $env:GATEWAY_URL = "http://127.0.0.1:$P_GATEWAY"
        $uvArgs = @('-m','uvicorn','app.main:app','--host','0.0.0.0','--port',"$P_BACKEND")
        if ($Dev) { $uvArgs += '--reload' }
        $uvLine = ($uvArgs | ForEach-Object { Quote-Arg $_ }) -join ' '
        Start-Bg -Name 'backend' -WorkDir $BACKEND_DIR -FilePath $PYTHON -ArgLine $uvLine | Out-Null
        Write-Note 'جارٍ التشغيل (قد يستغرق بعض الوقت عند أول إقلاع) ...'
    }
    if (Wait-Url $URL_BACKEND 120) {
        Write-Ok "الخادم الخلفي جاهز - $URL_BACKEND"
    } else {
        Write-Fail 'الخادم الخلفي لم يستجب خلال المهلة'
        Show-LogTail 'backend'
        return $false
    }

    # ----- 3) Gateway
    Write-Section '[3/4] بوابة الطلبات (Gateway :3001)'
    if (Test-Port $P_GATEWAY) {
        Write-Ok 'يعمل بالفعل - تم تخطي التشغيل'
    } else {
        $env:PYTHON_BACKEND_URL = "http://127.0.0.1:$P_BACKEND"
        $env:CORS_ORIGINS = "http://localhost:$P_FRONT,http://localhost:$P_GATEWAY,http://127.0.0.1:$P_FRONT"
        $tsxArgs = @('src\index.ts')
        if ($Dev) { $tsxArgs = @('watch','src\index.ts') }
        $tsxLine = (Quote-Arg $TSX_ENTRY) + ' ' + (($tsxArgs | ForEach-Object { Quote-Arg $_ }) -join ' ')
        Start-Bg -Name 'gateway' -WorkDir $GATEWAY_DIR -FilePath $NODE -ArgLine $tsxLine | Out-Null
        Write-Note 'جارٍ التشغيل ...'
    }
    if (Wait-Url $URL_GATEWAY 60) {
        Write-Ok "البوابة جاهزة - $URL_GATEWAY"
    } else {
        Write-Fail 'البوابة لم تستجب خلال المهلة'
        Show-LogTail 'gateway'
        return $false
    }

    # ----- 4) Frontend
    Write-Section '[4/4] الواجهة الأمامية (React/Vite :5173)'
    if (Test-Port $P_FRONT) {
        Write-Ok 'يعمل بالفعل - تم تخطي التشغيل'
    } else {
        $viteLine = (Quote-Arg $VITE_ENTRY) + " --port $P_FRONT --strictPort"
        Start-Bg -Name 'frontend' -WorkDir $FRONTEND_DIR -FilePath $NODE -ArgLine $viteLine | Out-Null
        Write-Note 'جارٍ التشغيل ...'
    }
    if (Wait-Url $URL_FRONT 90) {
        Write-Ok "الواجهة جاهزة - $URL_FRONT"
    } else {
        Write-Fail 'الواجهة لم تستجب خلال المهلة'
        Show-LogTail 'frontend'
        return $false
    }

    # ----- summary
    Write-Host ''
    Write-Host '========================================' -ForegroundColor Green
    Write-Host '   تم تشغيل النظام بنجاح' -ForegroundColor Green
    Write-Host '========================================' -ForegroundColor Green
    Write-Host "   الواجهة    : http://localhost:$P_FRONT" -ForegroundColor Cyan
    Write-Host "   الخلفية    : http://localhost:$P_BACKEND/docs" -ForegroundColor Cyan
    Write-Host "   البوابة    : http://localhost:$P_GATEWAY" -ForegroundColor Cyan
    Write-Host '   قاعدة البيانات : localhost:5432' -ForegroundColor Cyan
    Write-Host ''
    Write-Host "   السجلات : $LOG_DIR" -ForegroundColor DarkGray
    Write-Host '   للإيقاف : شغّل "إيقاف النظام.bat"' -ForegroundColor Yellow
    Write-Host '========================================' -ForegroundColor Green

    if (-not $NoBrowser) {
        try { Start-Process "http://localhost:$P_FRONT" } catch { }
    }
    return $true
}

# ------------------------------------------------------------------ main
# Explicit exits: falling off the end makes Windows PowerShell linger during
# teardown while detached child processes are still alive.
switch ($Action) {
    'start' {
        if (Invoke-Start) { exit 0 } else { exit 1 }
    }
    'stop' {
        Stop-AllServices
        exit 0
    }
    'restart' {
        Stop-AllServices
        Start-Sleep -Seconds 2
        if (Invoke-Start) { exit 0 } else { exit 1 }
    }
    'status' {
        Show-Status
        exit 0
    }
}
