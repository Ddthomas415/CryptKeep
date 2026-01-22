$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot) | Out-Null
Set-Location ..

python -m pip install --upgrade pip
python -m pip install pyinstaller

pyinstaller -y packaging\pyinstaller\crypto_bot_pro.spec

Write-Host "DONE: dist\CryptoBotPro\CryptoBotPro.exe"
