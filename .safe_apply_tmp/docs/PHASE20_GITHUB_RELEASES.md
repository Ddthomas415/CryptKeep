# Phase 20 — GitHub Release publishing (automatic)

Workflow:
- .github/workflows/publish_release.yml
- Trigger: push a tag like v1.2.3
- Builds:
  - Windows: PyInstaller dist folder zipped as CryptoBotPro-vX.Y.Z-windows-dist.zip
  - macOS: DMG renamed CryptoBotPro-vX.Y.Z-macos.dmg
- Publishes:
  - Creates a GitHub Release (auto notes)
  - Uploads both artifacts

Required:
- In repo settings, Actions must be allowed.
- The workflow uses `contents: write` permission to publish releases.

How to run:
- git tag v0.1.1
- git push origin v0.1.1
