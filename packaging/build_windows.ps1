# Run from repo root in PowerShell
py -m installers.bootstrap venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\pip.exe install -r requirements-dev.txt

.\.venv\Scripts\pyinstaller.exe --clean --noconfirm packaging\cryptobotpro.spec

Write-Host ""
Write-Host "Build complete."
Write-Host "Output: dist\CryptoBotPro\CryptoBotPro.exe"
