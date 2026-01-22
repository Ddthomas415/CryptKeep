# Phase 301 — Optional Packaged Desktop App

Default (recommended) install remains:
- one-command installer + Desktop launcher (Phase 300)

Optional packaged path:
- A small Python wrapper starts Streamlit and opens an embedded window (pywebview).
- Build with PyInstaller.

Files:
- packaging/desktop_wrapper.py
- requirements/desktop.txt
- packaging/pyinstaller/build.sh
- packaging/pyinstaller/build.ps1
- installers/install_desktop_extras.sh / .ps1

Build:
1) Install desktop extras:
   - macOS: bash installers/install_desktop_extras.sh
   - Windows: powershell -ExecutionPolicy Bypass -File installers\install_desktop_extras.ps1
2) Build:
   - macOS: bash packaging/pyinstaller/build.sh
   - Windows: powershell -ExecutionPolicy Bypass -File packaging/pyinstaller/build.ps1

Output:
- dist/CryptoBotPro (or CryptoBotPro.exe)
