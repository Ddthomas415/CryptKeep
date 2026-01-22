# Phase 38 — Signed Release Pipeline (Windows + macOS)

## Goals
- Produce a desktop build (PyInstaller) per OS.
- Sign executables/installers.
- Notarize macOS distribution (recommended for fewer Gatekeeper warnings).

## Windows (recommended flow)
1) Build:
   - python scripts/build_desktop.py

2) Sign EXE (requires cert + signtool):
   - powershell -ExecutionPolicy Bypass -File packaging/windows/sign_windows.ps1

3) Build installer:
   - Compile packaging/windows/inno_setup.iss in Inno Setup

4) Sign installer:
   - packaging/windows/sign_windows.ps1 (InstallerPath points to your compiled installer)
OR configure Inno Setup [Setup]: SignTool to sign automatically during compile.

Refs:
- Microsoft SignTool docs
- Inno Setup [Setup]: SignTool docs

## macOS (recommended flow)
1) Build on macOS:
   - python scripts/build_desktop.py

2) Sign + Notarize:
   - export MAC_SIGN_ID="Developer ID Application: ..."
   - export APPLE_ID="you@..."
   - export TEAM_ID="TEAMID"
   - export APP_SPECIFIC_PASSWORD="...."
   - bash packaging/macos/sign_and_notarize.sh dist/CryptoBotProDesktop/CryptoBotProDesktop

Refs:
- Apple notarization workflow (notarytool + stapler)
- Apple Developer ID overview

## Notes
- Signing requires paid certificates (Developer ID for Apple; Code Signing cert for Windows).
- Do NOT ship secrets in installers; keep using keyring/env.
