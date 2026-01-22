Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

$ExePath = "dist\CryptoBotPro\CryptoBotPro.exe"
if (!(Test-Path $ExePath)) {
  Write-Host "Missing $ExePath. Build first: .\scripts\build_windows.ps1"
  exit 2
}

# REQUIREMENTS:
# - A code signing cert installed (or available via Trusted Signing/Azure), and signtool.exe available.
# Microsoft docs: SignTool is the CLI used to sign + timestamp files. :contentReference[oaicite:4]{index=4}
# Smart App Control guidance emphasizes trusted signing. :contentReference[oaicite:5]{index=5}

$TimeStampUrl = $env:CBP_TIMESTAMP_URL
if ([string]::IsNullOrWhiteSpace($TimeStampUrl)) { $TimeStampUrl = "http://timestamp.digicert.com" }

Write-Host "==> Signing EXE: $ExePath"
# /a picks best cert automatically; replace with /sha1 or /n if you need to target a specific cert.
signtool sign /fd SHA256 /tr $TimeStampUrl /td SHA256 /a $ExePath

Write-Host "==> Verify signature"
signtool verify /pa /v $ExePath

Write-Host "DONE: signed $ExePath"
