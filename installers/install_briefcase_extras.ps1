Param()
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "ERROR: .venv not found. Run installers\install.ps1 first."
  exit 1
}
& .\.venv\Scripts\python.exe -m pip install -r requirements\briefcase.txt
Write-Host "[CryptoBotPro] Briefcase installed in this venv."
