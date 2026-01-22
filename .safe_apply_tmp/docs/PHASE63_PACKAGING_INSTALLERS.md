# Phase 63 — Installable app path (Mac + Windows)

Two supported paths:

## A) Recommended (most reliable): one-command install + run
- macOS:
  - From repo root:
    - `bash scripts/install.sh`
- Windows (PowerShell):
  - `Set-ExecutionPolicy -Scope Process Bypass`
  - `.\scripts\install.ps1`

This creates a local virtualenv + installs deps + launches:
- `python scripts/run_desktop.py`

The desktop runner starts Streamlit and opens a browser to the local URL.

## B) Optional native packaging (advanced): PyInstaller
Why optional:
- Streamlit uses a local server and packaging can be finicky; expect iteration on hiddenimports/data.

Build on the target OS:
- macOS:
  - `bash scripts/build_mac_app.sh`
- Windows:
  - `powershell -ExecutionPolicy Bypass -File scripts\build_windows_exe.ps1`

Outputs:
- `dist/CryptoBotPro/...`

Notes:
- PyInstaller builds are not reliably cross-compiled.
- If you hit missing-module issues, add packages to the collect_all list in:
  - `packaging/pyinstaller/crypto_bot_pro.spec`
