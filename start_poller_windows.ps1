Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)
py scripts\bootstrap.py poller
