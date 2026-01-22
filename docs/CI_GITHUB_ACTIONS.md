# Phase 307 — GitHub Actions CI

We ship two workflows:

## 1) CI - PyInstaller Desktop Wrapper (recommended)
File: `.github/workflows/ci-pyinstaller.yml`

- Runs on PR + main pushes.
- Builds a desktop wrapper binary via `scripts/release_checklist.py --pyinstaller`
- Uploads:
  - dist/**
  - releases/release_manifest_*.json

## 2) CI - Briefcase Package (optional/heavier)
File: `.github/workflows/ci-briefcase.yml`

- Manual only (`workflow_dispatch`).
- Windows uses ZIP packaging to avoid MSI/WiX toolchain friction.
- macOS uses default packaging (typically DMG for GUI apps).

Signing/notarization in CI:
- Keep signing secrets in GitHub Actions Secrets.
- Our repo supports *local* signing scripts and opt-in release hooks (Phase 306).
- CI signing is a later step if/when you want it (fail-closed, secrets never stored in repo).
