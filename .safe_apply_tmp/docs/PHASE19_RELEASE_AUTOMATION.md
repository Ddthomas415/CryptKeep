# Phase 19 — Release automation + versioning + CI

Single source of truth:
- VERSION file (X.Y.Z)

Commands:
- Set explicit version:
  - python scripts/set_version.py 1.2.3
- Bump:
  - python scripts/bump_version.py patch|minor|major

Propagation:
- Updates packaging/inno/CryptoBotPro.iss MyAppVersion define
- Adds/updates "Version: X.Y.Z" line in docs/CHAT_HANDOFF.md (near top)
- Dashboard footer shows version

CI:
- .github/workflows/ci.yml -> validates on PR/main (Linux)
- .github/workflows/release.yml -> builds Windows dist folder and macOS DMG on tags vX.Y.Z
