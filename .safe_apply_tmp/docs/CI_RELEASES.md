# Phase 330 — CI Releases (GitHub Actions)

Trigger:
- Push a git tag like `v0.1.0` to build and publish a release.

Pipeline:
1) Windows job:
   - Installs Inno Setup via Chocolatey
   - Runs `scripts/build_windows_installer.ps1`
   - Uploads `dist_installers/*.exe` as artifact

2) macOS job:
   - Runs `scripts/build_macos_dmg.sh` (create-dmg optional; hdiutil fallback)
   - Uploads `dist_installers/*.dmg` as artifact

3) release job:
   - Downloads both artifacts
   - Publishes a GitHub Release and attaches assets

Permissions:
- Workflow sets `permissions: contents: write` (required for release uploads).
- Repo setting must allow `GITHUB_TOKEN` read/write if your org restricts it.

How to cut a release:
- `git tag v0.1.0`
- `git push origin v0.1.0`
