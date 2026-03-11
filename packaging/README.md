# Packaging

Desktop packaging entrypoints and helpers live here.

Primary config:
- `packaging/config/app.json`

Primary build entrypoint:
- `packaging/pyinstaller/build.py`

Top-level wrappers:
- macOS/Linux: `scripts/build_app.sh`
- Windows: `scripts/build_app.ps1`

macOS app bundle build:
- `scripts/build_macos.sh` (forces windowed mode and produces `dist/CryptoBotPro.app`)

Notes:
- Build on the target OS (no cross-build assumptions).
- Icons are optional:
  - `packaging/assets/icon.icns`
  - `packaging/assets/icon.ico`
