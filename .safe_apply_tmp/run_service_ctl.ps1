param(
  [Parameter(Mandatory=$true)][string]$cmd,
  [string]$name = ""
)
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Write-Host "ERROR: .venv not found. Run: py scripts\install.py"
  exit 1
}
$argsList = @($cmd)
if ($name -ne "") { $argsList += @("--name", $name) }
& $py scripts\service_ctl.py @argsList
