Param()
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "ERROR: .venv not found. Run installers\install.ps1 first."
  exit 1
}
call .\.venv\Scripts\activate.bat
briefcase create windows
briefcase build windows
briefcase package windows
Write-Host "Done. Check build\cryptobotpro\windows\ (or briefcase output paths)."
