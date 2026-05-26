# Build a Windows executable via PyInstaller (run on Windows)
# Requirements:
#   python -m pip install pyinstaller
#
# Build:
#   powershell -ExecutionPolicy Bypass -File scripts\build_windows_exe.ps1

$ErrorActionPreference = "Stop"
python -m pip install --upgrade pyinstaller
pyinstaller --noconfirm packaging/pyinstaller/crypto_bot_pro.spec

Write-Host "OK: Build finished."
Write-Host "Output: dist\CryptoBotPro\CryptoBotPro.exe"
