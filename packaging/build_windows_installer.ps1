$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ROOT

$APP_VERSION = (python scripts\get_version.py).Trim()
$env:APP_VERSION = $APP_VERSION

# Ensure PyInstaller build exists
if (-not (Test-Path "dist\CryptoBotPro")) {
  powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
}

# Compile installer:
# ISCC.exe is the official CLI compiler :contentReference[oaicite:5]{index=5}
# If ISCC is not on PATH, install Inno Setup and run again.
iscc "packaging\inno\CryptoBotPro.iss"

Write-Host "DONE: release\CryptoBotPro-$APP_VERSION-Windows-Setup.exe"
