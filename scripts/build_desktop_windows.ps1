# Compatibility wrapper for scripts\release\build_desktop_windows.ps1.
# Uses requirements\desktop.txt in the release wrapper.
$ErrorActionPreference = "Stop"
$ROOT = (Get-Item $PSScriptRoot).Parent.FullName
& "$ROOT\scripts\release\build_desktop_windows.ps1" @args
