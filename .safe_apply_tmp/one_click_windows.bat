@echo off
setlocal
cd /d %~dp0
py scripts\bootstrap.py run
endlocal
