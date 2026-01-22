Param()

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "ERROR: .venv not found. Run installers\install.ps1 first."
  exit 1
}

$req = $null
if (Test-Path "requirements.txt") { $req = "requirements.txt" }
elseif (Test-Path "requirements\base.txt") { $req = "requirements\base.txt" }

if ($req) {
  & .\.venv\Scripts\python.exe -m pip install --upgrade -r $req
  Write-Host "[CryptoBotPro] Updated dependencies from $req"
} else {
  Write-Host "WARNING: No requirements file found."
}
