# Phase 77 — Real installers + CI releases

## Windows
- Installer: Inno Setup `.iss`, compiled by ISCC.exe :contentReference[oaicite:7]{index=7}
- CI compiles `.iss` using Inno Setup GitHub Action :contentReference[oaicite:8]{index=8}

Local build:
- `powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1` (PyInstaller)
- `powershell -ExecutionPolicy Bypass -File packaging/build_windows_installer.ps1` (Inno setup)

## macOS
- DMG built with dmgbuild :contentReference[oaicite:9]{index=9}

Local build:
- `bash packaging/build_macos.sh` (PyInstaller)
- `bash packaging/build_dmg.sh` (DMG)

## CI
- `.github/workflows/release.yml` builds on tags `v*` and publishes release assets.

## Release outputs
- release/*.dmg
- release/*Windows-Setup.exe
- release/manifest.json (hashes for updater-ready workflow)
