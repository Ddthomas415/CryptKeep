param(
  [int]$IntervalMinutes = 5
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$TaskName = "CryptoBotPro-Monitor"

# Find python in PATH
$Python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $Python) { $Python = (Get-Command python3 -ErrorAction SilentlyContinue)?.Source }
if (-not $Python) { throw "Python not found in PATH. Install Python 3 and ensure 'python' is available." }

$Action = New-ScheduledTaskAction -Execute $Python -Argument "scripts\monitor_and_maybe_rollback.py" -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)

# Run only when user is logged on (simpler + safer)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "CryptoBotPro paper monitor + rollback guardrails" -Force | Out-Null

Write-Host "OK: Installed Windows scheduled task '$TaskName' every $IntervalMinutes minutes."
Write-Host "RepoRoot: $RepoRoot"
