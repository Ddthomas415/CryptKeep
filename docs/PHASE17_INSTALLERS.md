# Phase 17 — Installers (Windows + macOS)

## Windows (Installer EXE)
Tool: Inno Setup (script-based installer; supports shortcuts/uninstall). 
Workflow:
1) Build app: packaging/pyinstaller/build_windows.ps1  -> dist\CryptoBotPro\CryptoBotPro.exe
2) Build installer: packaging/inno/build_windows_installer.ps1 -> dist_installer\CryptoBotPro-Setup-*.exe
Notes:
- Keep AppId stable across versions so upgrades behave cleanly.

## macOS (.app + .dmg)
Workflow:
1) Build .app: pyinstaller (spec: packaging/pyinstaller/crypto_bot_pro_macos.spec)
2) Build dmg: packaging/macos/build_app_and_dmg.sh (uses hdiutil)

Signing/notarization (required for easy installs on other Macs):
- codesign the .app
- notarize (and staple) then create/notarize the .dmg
Keep these steps explicit and controlled (no automation without certs present).
