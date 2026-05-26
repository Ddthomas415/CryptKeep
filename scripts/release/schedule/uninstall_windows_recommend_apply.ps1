$ErrorActionPreference = "Stop"
$TaskName = "CryptoBotPro-RecommendApply"
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
Write-Host "OK: Uninstalled Windows scheduled task '$TaskName' (if it existed)."
