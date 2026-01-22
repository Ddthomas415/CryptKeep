Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

$Msix = "dist\CryptoBotPro.msix"
if (!(Test-Path $Msix)) {
  Write-Host "ERROR: Missing $Msix"
  exit 2
}

Write-Host "==> Installing (Add-AppxPackage)"
Add-AppxPackage -Path $Msix

Write-Host "DONE: Installed. Launch from Start Menu: CryptoBotPro"
