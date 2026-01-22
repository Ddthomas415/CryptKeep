# Usage (PowerShell):
#   Set-ExecutionPolicy -Scope Process Bypass
#   ./scripts/install.ps1

$ErrorActionPreference = "Stop"

$Python = $env:PYTHON_BIN
if (-not $Python) { $Python = "python" }

# Verify python
try { & $Python --version | Out-Null } catch { throw "Python not found. Install Python 3.11+ and re-run." }

$Venv = $env:VENV_DIR
if (-not $Venv) { $Venv = ".venv" }

if (-not (Test-Path $Venv)) {
  & $Python -m venv $Venv
}

$Pip = Join-Path $Venv "Scripts\pip.exe"
$Py  = Join-Path $Venv "Scripts\python.exe"

& $Pip install --upgrade pip wheel setuptools

if (Test-Path "requirements.txt") {
  & $Pip install -r "requirements.txt"
} else {
  throw "requirements.txt not found"
}

Write-Host "OK: Installed. Launching desktop runner..."
& $Py "scripts\run_desktop.py"
