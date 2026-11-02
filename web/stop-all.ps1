# Compatibility wrapper - delegates to erp.ps1
# Kept so existing shortcuts / documentation that call stop-all.ps1 keep working.

$target = Join-Path $PSScriptRoot 'erp.ps1'
& $target -Action stop
exit $LASTEXITCODE
