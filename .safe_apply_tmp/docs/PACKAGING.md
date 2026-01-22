# Packaging (Updated Phase 281)

## Fastest reliable route (per-OS build)
We build per OS using PyInstaller. You build Windows artifacts on Windows, macOS artifacts on macOS.

## One command build
- macOS/Linux: `bash scripts/build_app.sh`
- Windows PowerShell: `powershell -ExecutionPolicy Bypass -File scripts/build_app.ps1`

## Windowed vs console
- Default is console (best for debugging).
- To build windowed:
  - macOS/Linux: `CBP_WINDOWED=1 bash scripts/build_app.sh`
  - Windows (PowerShell): `$env:CBP_WINDOWED="1"; powershell -ExecutionPolicy Bypass -File scripts/build_app.ps1`

## Icons / version resources (optional)
- Configure in `packaging/config/app.json`
- Place icons:
  - Windows: `packaging/assets/icon.ico` (real ICO)
  - macOS: `packaging/assets/icon.icns` (real ICNS)
- Windows version info template: `packaging/windows/version_info.txt` (used automatically if present)

## Output
- `dist/CryptoBotPro/` (onedir)
