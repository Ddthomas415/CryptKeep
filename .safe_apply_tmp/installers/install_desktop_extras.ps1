Param()
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "ERROR: .venv not found. Run installers\install.ps1 first."
  exit 1
}
& .\.venv\Scripts\python.exe -m pip install -r requirements\desktop.txt
Write-Host "[CryptoBotPro] Desktop build extras installed."
