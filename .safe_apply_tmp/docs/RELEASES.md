# Releases (Phase 344)

CI Workflows:
- `.github/workflows/release.yml`
  - Trigger: push tag `v*` (example: `v1.0.0`)
  - Builds:
    - macOS: `CryptoBotPro-macOS.app.zip`
    - Windows: `CryptoBotPro-Windows-console.zip`
    - Windows: `CryptoBotPro-Windows-quiet.zip`
  - Creates (or updates) a GitHub Release for that tag and uploads the assets.

- `.github/workflows/nightly.yml`
  - Trigger: daily 02:00 UTC + manual dispatch
  - Produces artifacts only (no release).

How to cut a release:
1) Commit and push your changes to main.
2) Tag and push a version:
   - `git tag v1.0.0`
   - `git push origin v1.0.0`
3) GitHub Actions will build and attach artifacts to the Release.

Notes:
- Builds must run on each OS (macOS builds on macOS runner; Windows builds on Windows runner).
- Optional icons are used automatically if present in `packaging/icons/`.
