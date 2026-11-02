# Compatibility wrapper - delegates to erp.ps1
# Kept so existing shortcuts / documentation that call start-all.ps1 keep working.
param(
    [switch]$Dev,
    [switch]$NoBrowser
)

$target = Join-Path $PSScriptRoot 'erp.ps1'
& $target -Action start -Dev:$Dev -NoBrowser:$NoBrowser
exit $LASTEXITCODE
