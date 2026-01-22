Param()
$ErrorActionPreference = "Stop"
$Root = Resolve-Path $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "ERROR: .venv not found. Run installer first."
  exit 2
}
& .\.venv\Scripts\python.exe -m services.trading_runner.run_trader --config config\trading.yaml
