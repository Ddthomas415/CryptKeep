$ErrorActionPreference="Stop"
py -m pip install -r requirements-dev.txt
py packaging/pyinstaller/build.py
Write-Host "DONE. Run from dist\CryptoBotPro\ (or create installer next)."
