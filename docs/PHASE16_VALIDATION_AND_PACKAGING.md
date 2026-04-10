# Phase 16 — Validation + packaging

One-command validation:
- macOS/Linux:  ./scripts/validate.sh
- Windows:      .\scripts\validate.ps1
- Or:           python scripts/validate.py

Preflight alone:
- python scripts/preflight.py
  - uses merged runtime trading config and accepts `.cbp_state/runtime/config/user.yaml` when the legacy file is absent

Packaging (PyInstaller):
- macOS:  bash packaging/pyinstaller/build_macos.sh
- Windows: powershell -ExecutionPolicy Bypass -File packaging\pyinstaller\build_windows.ps1

Launcher:
- app_launcher/launcher.py
- Starts Streamlit and opens the browser. Includes multiprocessing.freeze_support() to reduce Windows/PyInstaller issues. :contentReference[oaicite:6]{index=6}
