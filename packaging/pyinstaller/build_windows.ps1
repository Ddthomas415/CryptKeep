$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot) | Out-Null
Set-Location ..

$Py = if (Test-Path ".venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "py" }

& $Py -m pip install --upgrade pip
& $Py -m pip install -r requirements\desktop.txt

& $Py packaging\pyinstaller\build.py

Write-Host "DONE: dist\CryptoBotPro\"
