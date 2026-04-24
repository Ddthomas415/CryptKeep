$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot) | Out-Null
Set-Location ..


$ver = (Get-Content VERSION -ErrorAction SilentlyContinue)
if (-not $ver) { $ver = "0.0.0" }
Write-Host "[release] version: $ver"

python scripts\validate.py

# Build PyInstaller output
powershell -ExecutionPolicy Bypass -File packaging\pyinstaller\build_windows.ps1

$exe = "dist\CryptoBotPro\CryptoBotPro.exe"

function Find-SignTool {
  if ($env:SIGNTOOL_PATH -and (Test-Path $env:SIGNTOOL_PATH)) { return $env:SIGNTOOL_PATH }
  $candidates = @(
    "$env:ProgramFiles (x86)\Windows Kits\10\bin\x64\signtool.exe",
    "$env:ProgramFiles\Windows Kits\10\bin\x64\signtool.exe"
  )
  foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
  return $null
}

$signtool = Find-SignTool

# Optional: sign the EXE
if ($signtool -and (Test-Path $exe) -and $env:WIN_CERT_PFX -and (Test-Path $env:WIN_CERT_PFX)) {
  $ts = $env:WIN_TIMESTAMP_URL
  if (-not $ts) { $ts = "http://timestamp.digicert.com" } # override if your CA specifies a different URL
  Write-Host "[release] signing EXE with signtool..."
  & $signtool sign /fd sha256 /td sha256 /tr $ts /f $env:WIN_CERT_PFX /p $env:WIN_CERT_PASSWORD $exe
  & $signtool verify /pa /v $exe
} else {
  Write-Host "[release] SKIP signing (set SIGNTOOL_PATH optional, WIN_CERT_PFX, WIN_CERT_PASSWORD)"
}

# Build installer (Inno Setup)
powershell -ExecutionPolicy Bypass -File packaging\inno\build_windows_installer.ps1

Write-Host "[release] DONE: dist_installer\CryptoBotPro-Setup-*.exe"
