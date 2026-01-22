# Phase 329 — Real Installers (Windows + macOS)

## Windows (Installer EXE)
Tool: Inno Setup (script-based installer).  
- Build the app: `scripts/build_windows.ps1`
- Build installer: `scripts/build_windows_installer.ps1`
Outputs:
- `dist_installers/CryptoBotPro-Setup.exe`

Notes:
- The installer packages the entire PyInstaller `dist/CryptoBotPro/` folder.
- Adds Start Menu and optional Desktop shortcuts.

## macOS (.app + .dmg)
Toolchain:
- PyInstaller builds the executable + `.app` bundle on macOS when `--windowed` is used.
- DMG built by `create-dmg` if available, otherwise by `hdiutil` fallback.

Build:
- `bash scripts/build_macos_dmg.sh`

Outputs:
- `dist_installers/CryptoBotPro.dmg`

## Optional: Signing + Notarization (recommended for distribution)
Apple workflow (high-level):
1) Code sign the `.app` bundle (Developer ID certificate).
2) Notarize using `xcrun notarytool submit --wait`.
3) Staple ticket using `xcrun stapler staple`.
(Apple docs cover details for notarization and stapling.) 

Important:
- Notarization requirements and exact commands depend on your Apple Developer setup.
