$ErrorActionPreference = "Stop"
$Root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $Root

$Py = if (Test-Path ".venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "py" }

& $Py -m pip install --upgrade pip
& $Py scripts\sync_briefcase_requires.py
& $Py -m pip install briefcase
& $Py -m pip install -r requirements\briefcase.txt

Write-Host "Done: briefcase extras installed."
