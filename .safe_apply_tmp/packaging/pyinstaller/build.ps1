Param()

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "ERROR: .venv not found. Run installers\install.ps1 first."
  exit 1
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements\desktop.txt

& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean `
  --name CryptoBotPro `
  --onefile `
  --hidden-import streamlit `
  --hidden-import webview `
  packaging\desktop_wrapper.py

Write-Host "Built: dist\CryptoBotPro.exe"
