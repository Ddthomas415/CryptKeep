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
- Supply-chain verification policy is documented in
  `docs/SUPPLY_CHAIN_RELEASE_POLICY.md`; adding a dependency-audit or
  hash-locked install gate remains a separate reviewed CI change.

## Required PR Check Fast Path

The required PR checks keep their stable branch-protection names, but the
heaviest workflows now classify pull-request file changes before installing
dependencies or running tests.

Docs-only PRs are allowed to fast-pass these checks:

- `CI validate`
- `CI sanity`
- `Build (macos-latest)`
- `Build (windows-latest)`

The fast path is intentionally narrow. It applies only when every changed file
is documentation-like:

- `docs/*`
- `*.md`
- `README*`
- `CHANGELOG*`
- `LICENSE*`
- `NOTICE*`

Any source, script, config, workflow, test, strategy, execution, risk, or
packaging change takes the full CI path. This preserves the existing required
check names so branch protection does not wait on skipped workflows.
