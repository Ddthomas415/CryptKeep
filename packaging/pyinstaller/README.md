# PyInstaller Desktop Wrapper Build (Optional)

This builds a single executable that launches:
- a local Streamlit server (same Python runtime)
- an embedded desktop window (pywebview)

## Install build extras (recommended in a clean venv)
- pip install -r requirements/desktop.txt

## Build
- macOS/Linux: bash packaging/pyinstaller/build.sh
- Windows: powershell -ExecutionPolicy Bypass -File packaging/pyinstaller/build.ps1

Output:
- dist/CryptoBotPro (or CryptoBotPro.exe)
