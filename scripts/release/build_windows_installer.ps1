# Phase 329: Build Windows installer using Inno Setup (ISCC)
# Usage (PowerShell, from repo root):
#   powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/build_windows_installer.ps1

$ErrorActionPreference = "Stop"

# 1) Ensure app is built (PyInstaller onedir)
powershell -ExecutionPolicy Bypass -File scripts\build_app.ps1

# 2) Find ISCC.exe
$possible = @(
  "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$iscc = $null
foreach ($p in $possible) {
  if (Test-Path $p) { $iscc = $p; break }
}

if (-not $iscc) {
  Write-Host "ERROR: ISCC.exe not found. Install Inno Setup, then re-run." -ForegroundColor Red
  exit 1
}

# 3) Compile installer
& $iscc "packaging\windows\cryptobotpro.iss"

Write-Host "Installer built. See dist_installers\CryptoBotPro-Setup.exe" -ForegroundColor Green
