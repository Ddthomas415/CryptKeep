# Briefcase Native Installers (Optional)

Briefcase builds *native* installers:
- Windows: MSI (default) or ZIP
- macOS: DMG (default for GUI), ZIP, or PKG

This repo uses a thin desktop wrapper entry (src/cryptobotpro_desktop/app.py) that starts the Streamlit UI and embedded window.

## 1) Install Briefcase (in your existing .venv)
- macOS: bash installers/install_briefcase_extras.sh
- Windows: powershell -ExecutionPolicy Bypass -File installers\install_briefcase_extras.ps1

## 2) Create/build/package
From repo root (after briefcase install):

### macOS
- briefcase create macOS
- briefcase build macOS
- briefcase package macOS   (default: dmg for GUI apps)

### Windows
- briefcase create windows
- briefcase build windows
- briefcase package windows (default: MSI)

Notes:
- Windows MSI requires additional system tooling (WiX and Windows prerequisites).
- If packaging fails, keep using Phase 300 (one-command install + Desktop launcher).
