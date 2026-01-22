Param()

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "[CryptoBotPro] Installing into: $Root"

# Require Python launcher
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
  Write-Host "ERROR: Python launcher 'py' not found. Install Python 3.11+ from python.org and re-run."
  exit 1
}

# Create venv
if (-not (Test-Path ".venv")) {
  Write-Host "[CryptoBotPro] Creating virtualenv..."
  py -3 -m venv .venv
}

# Activate + upgrade pip
& .\.venv\Scripts\python.exe -m pip install --upgrade pip wheel setuptools

# Requirements
$req = $null
if (Test-Path "requirements.txt") { $req = "requirements.txt" }
elseif (Test-Path "requirements\base.txt") { $req = "requirements\base.txt" }

if ($req) {
  Write-Host "[CryptoBotPro] Installing dependencies from $req ..."
  & .\.venv\Scripts\python.exe -m pip install -r $req
} else {
  Write-Host "WARNING: No requirements file found. Skipping pip install."
}

# Create start.cmd (repo-local)
$startCmd = Join-Path $Root "installers\start.cmd"
@"
@echo off
setlocal
cd /d ""%~dp0\..""
call .venv\Scripts\activate.bat
python -m streamlit run dashboard\app.py --server.port 8501
endlocal
"@ | Set-Content -Encoding ASCII $startCmd

# Create Desktop shortcut -> start.cmd (WScript.Shell CreateShortcut)
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "CryptoBotPro.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $startCmd
$Shortcut.WorkingDirectory = (Join-Path $Root "")
$Shortcut.Save()

Write-Host "[CryptoBotPro] Done."
Write-Host "Desktop shortcut created: $ShortcutPath"
Write-Host "Double-click it to start the dashboard."
