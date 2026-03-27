$ErrorActionPreference="Stop"
$Root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $Root

$Py = if (Test-Path ".venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "py" }

& $Py -m pip install --upgrade pip
if (Test-Path "requirements\\desktop.txt") {
  & $Py -m pip install -r requirements\desktop.txt
} elseif (Test-Path "requirements.txt") {
  & $Py -m pip install -r requirements.txt
} else {
  & $Py -m pip install pyinstaller
}

& $Py packaging/pyinstaller/build.py
Write-Host "DONE. Output is in dist\."
