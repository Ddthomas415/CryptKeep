$ErrorActionPreference = "Stop"

# Run from repo root: powershell -ExecutionPolicy Bypass -File packaging\inno\build_windows_installer.ps1

$common = @(
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
  "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$iscc = $null
foreach ($p in $common) { if (Test-Path $p) { $iscc = $p; break } }

if (-not $iscc) {
  Write-Host "ERROR: ISCC.exe not found. Install Inno Setup 6, then re-run." -ForegroundColor Red
  exit 2
}

# Ensure PyInstaller dist exists
if (-not (Test-Path ".\dist\CryptoBotPro\CryptoBotPro.exe")) {
  Write-Host "ERROR: PyInstaller output not found. Build first: powershell -ExecutionPolicy Bypass -File packaging\pyinstaller\build_windows.ps1" -ForegroundColor Red
  exit 2
}

New-Item -ItemType Directory -Force -Path ".\dist_installer" | Out-Null

& $iscc "packaging\inno\CryptoBotPro.iss"

Write-Host "DONE: dist_installer\CryptoBotPro-Setup-*.exe" -ForegroundColor Green
