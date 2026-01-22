Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

function Find-Tool($name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

$SignTool = Find-Tool "signtool.exe"
if (-not $SignTool) {
  Write-Host "ERROR: signtool.exe not found on PATH."
  Write-Host "Install Windows SDK (Signing Tools), then re-run."
  exit 2
}

$Msix = "dist\CryptoBotPro.msix"
if (!(Test-Path $Msix)) {
  Write-Host "ERROR: Missing $Msix"
  Write-Host "Build first: .\scripts\build_msix.ps1"
  exit 2
}

$TimeStampUrl = $env:CBP_TIMESTAMP_URL
if ([string]::IsNullOrWhiteSpace($TimeStampUrl)) { $TimeStampUrl = "http://timestamp.digicert.com" }

Write-Host "==> Signing MSIX: $Msix"
# /a selects best cert automatically; replace with /sha1 or /n as needed.
& $SignTool sign /fd SHA256 /tr $TimeStampUrl /td SHA256 /a $Msix | Out-Host

Write-Host "==> Verify signature"
& $SignTool verify /pa /v $Msix | Out-Host

Write-Host "DONE: signed $Msix"
