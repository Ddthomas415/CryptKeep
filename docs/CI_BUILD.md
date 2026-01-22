# CI Builds (GitHub Actions)

Workflow:
- `.github/workflows/build-desktop-app.yml`

It builds:
- Windows `.exe` (inside `dist/`)
- macOS `.app` (inside `dist/`)

Then zips the entire `dist/` folder into `dist_artifacts/*.zip` and uploads as a GitHub Actions artifact.

## Where to download
GitHub → Actions → pick a run → Artifacts.

## Notes
- These artifacts are **unsigned**; Windows SmartScreen and macOS Gatekeeper may warn.
- Signing/notarization can be added later (separate phase).
