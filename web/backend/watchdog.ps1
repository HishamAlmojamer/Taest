$ErrorActionPreference = 'SilentlyContinue'
$log = Join-Path $PSScriptRoot 'watchdog.log'
$state = Join-Path $PSScriptRoot 'watchdog.state'

function Write-Log($msg) {
    $line = "{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $log -Value $line -Encoding UTF8
    if ((Get-Item $log).Length -gt 1MB) {
        Get-Content $log -Tail 500 | Set-Content $log -Encoding UTF8
    }
}

function Probe {
    # Use Invoke-WebRequest (no external curl dependency) and 127.0.0.1 to
    # avoid IPv6 localhost resolution issues. Returns "<status> <seconds>".
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8001/api/health' -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
        $sw.Stop()
        return ("{0} {1:N3}" -f [int]$resp.StatusCode, $sw.Elapsed.TotalSeconds)
    } catch {
        return '000 0.000'
    }
}

# Keep the backend resident: raise priority so Windows pages it back in fast
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'run_service\.py|uvicorn' } |
    ForEach-Object {
        $proc = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
        if ($proc -and $proc.PriorityClass -ne 'AboveNormal') {
            $proc.PriorityClass = 'AboveNormal'
        }
    }

$result = Probe
$parts = $result -split '\s+'
if ($parts[0] -eq '200') {
    $t = 0.0
    if ($parts.Length -gt 1) { [void][double]::TryParse($parts[1], [ref]$t) }
    if ($t -gt 5) { Write-Log ("SLOW health={0}s" -f $t) }
    exit 0
}

# First probe failed (timeout/refused): verify once more after 10s.
# A single slow probe must never trigger a restart.
Start-Sleep -Seconds 10
$result2 = Probe
if ((($result2 -split '\s+')[0]) -eq '200') { exit 0 }

# Cooldown: restart at most once every 4 minutes (prevents restart loops
# while the process is still booting or the host is under memory pressure).
if (Test-Path $state) {
    $last = [datetime]::Parse((Get-Content $state -Raw).Trim())
    if (((Get-Date) - $last).TotalMinutes -lt 4) { exit 0 }
}

Write-Log ("DOWN probe1='{0}' probe2='{1}' -> restarting backend" -f $result, $result2)
Set-Content -Path $state -Value (Get-Date).ToString('o')

# NOTE: never call Stop-ScheduledTask / Start-ScheduledTask from this loop.
# Those cmdlets can block for many minutes (MSFT_Task scheduler bridge hangs
# in some sessions), which freezes the watchdog and leaves the backend down.
# Manage the backend process directly instead.
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'run_service\.py|uvicorn' } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
Start-Sleep -Seconds 2

$pyw = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
$svc = Join-Path $PSScriptRoot 'run_service.py'
# Convert to the 8.3 short path: Start-Process fails on long paths that mix
# Arabic characters when launched from a hidden/system session.
$root83 = $PSScriptRoot
try {
    $root83 = (New-Object -ComObject Scripting.FileSystemObject).GetFolder($PSScriptRoot).ShortPath
} catch { }
if (Test-Path $pyw) {
    Start-Process -FilePath (Join-Path $root83 '.venv\Scripts\pythonw.exe') `
        -ArgumentList (Join-Path $root83 'run_service.py') `
        -WorkingDirectory $root83 -WindowStyle Hidden
    Write-Log ("backend relaunched via {0} (short path)" -f $root83)
} else {
    # Fallback for environments without the virtualenv: system python.
    Start-Process -FilePath 'python' -ArgumentList $svc `
        -WorkingDirectory $root83 -WindowStyle Hidden
    Write-Log "backend relaunched via system python (venv missing)"
}

# Patient boot wait (first boot can take ~40s under load)
$up = $false
$waited = 0
for ($i = 1; $i -le 24; $i++) {
    Start-Sleep -Seconds 5
    $waited = $i * 5
    if ((Probe -split '\s+')[0] -eq '200') { $up = $true; break }
}
if ($up) {
    Write-Log ("restart done, health=200 after {0}s" -f $waited)
} else {
    Write-Log "restart issued; still down after 120s (cooldown active, will recheck next cycle)"
}
