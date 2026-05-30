# Compatibility wrapper for scripts\release\build_windows_installer.ps1.
# Contract: invokes scripts\build_app.ps1 through the release wrapper.
$ErrorActionPreference = "Stop"
$ROOT = (Get-Item $PSScriptRoot).Parent.FullName
& "$ROOT\scripts\release\build_windows_installer.ps1" @args
