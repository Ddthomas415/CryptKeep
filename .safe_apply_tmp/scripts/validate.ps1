$ErrorActionPreference="Stop"
Set-Location (Split-Path $PSScriptRoot) | Out-Null
Set-Location ..
python scripts\validate.py
