param(
  [int]$IntervalMinutes = 30
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$TaskName = "CryptoBotPro-RecommendApply"

$Python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $Python) { $Python = (Get-Command python3 -ErrorAction SilentlyContinue)?.Source }
if (-not $Python) { throw "Python not found in PATH. Install Python 3 and ensure 'python' is available." }

# Run recommend then apply_pending (apply requires explicit approval file + match)
$Args = "-c `"cd('$RepoRoot'); import subprocess; subprocess.check_call(['$Python','scripts\\recommend_model_switch.py']); subprocess.check_call(['$Python','scripts\\apply_pending_model_switch.py'])`""
$Action = New-ScheduledTaskAction -Execute $Python -Argument $Args -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "CryptoBotPro model recommend+apply (apply requires approval file)" -Force | Out-Null

Write-Host "OK: Installed Windows scheduled task '$TaskName' every $IntervalMinutes minutes (approval required to switch)."
Write-Host "RepoRoot: $RepoRoot"
