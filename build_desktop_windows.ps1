Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)
py scripts\bootstrap.py install
.\.venv\Scripts\python.exe -m pip install --upgrade pyinstaller pywebview
.\.venv\Scripts\python.exe scripts\build_desktop.py
Write-Host "DONE. See dist_desktop\"
