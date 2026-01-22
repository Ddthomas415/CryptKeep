# Build Windows exe locally (must run on Windows)
# Output: dist\CryptoBotPro.exe
$ErrorActionPreference = "Stop"

$ROOT = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $ROOT

$PY = if ($env:PYTHON) { $env:PYTHON } else { "py" }

if (!(Test-Path ".venv")) {
  & $PY -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip wheel
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip install pyinstaller

& .\.venv\Scripts\pyinstaller.exe --noconfirm packaging\pyinstaller\crypto_bot_pro.spec

Write-Host ""
Write-Host "Built: $ROOT\dist\CryptoBotPro.exe"
Write-Host "Run:   $ROOT\dist\CryptoBotPro.exe"
