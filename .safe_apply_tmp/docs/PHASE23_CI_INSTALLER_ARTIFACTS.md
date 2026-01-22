# Phase 23 — CI builds + signs installer artifact + publishes

Changes:
- publish_release.yml now builds:
  - Windows dist zip
  - Windows installer EXE (Inno Setup installed in CI)
  - macOS DMG
- Publishes all 3 assets to the GitHub Release.

Signing:
- Windows EXE signing remains optional (secrets-gated).
- Windows installer signing happens in build_windows_installer.ps1 (optional; env-driven).

UI:
- Release Train now includes OS-gated local build buttons:
  - Windows: build PyInstaller app, build Inno installer
  - macOS: build DMG
