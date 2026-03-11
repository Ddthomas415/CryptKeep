Param()

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

$Py = if (Test-Path ".venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "py" }

& $Py -m pip install --upgrade pip
if (Test-Path "requirements\desktop.txt") {
  & $Py -m pip install -r requirements\desktop.txt
} else {
  & $Py -m pip install -r requirements.txt
}

& $Py packaging/pyinstaller/build.py

Write-Host "Built: dist\CryptoBotPro\"
