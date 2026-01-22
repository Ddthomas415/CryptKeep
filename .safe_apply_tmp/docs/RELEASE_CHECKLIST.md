# Phase 304 — Release Checklist Automation

Script:
- `python scripts/release_checklist.py [options]`

Common runs:

## Non-destructive release manifest (no changes)
- `python scripts/release_checklist.py --dry-run`

## Patch bump + requires sync (recommended before packaging)
- `python scripts/release_checklist.py --bump patch --sync-requires`

## Build PyInstaller wrapper (optional)
- `python scripts/release_checklist.py --pyinstaller`

## Build Briefcase native package (optional; requires platform prerequisites)
- `python scripts/release_checklist.py --briefcase`

## Full run (patch bump + sync + package)
- `python scripts/release_checklist.py --bump patch --sync-requires --briefcase`

Outputs:
- Writes a manifest JSON under `releases/`:
  - build metadata
  - step results (stdout/stderr truncated)
  - artifact SHA-256 hashes for everything in dist/, build/, data/reconcile_reports/

## Opt-in signing/notarization (Phase 306)
Signing is FAIL-CLOSED and requires env vars. Nothing is stored in the repo.

### Windows signing
- Set: `RELEASE_SIGN_WINDOWS=1`
- Provide either:
  - `SIGN_PFX_PATH` + `SIGN_PFX_PASSWORD`, OR
  - `SIGN_CERT_THUMBPRINT`
- Optional:
  - `SIGN_TIMESTAMP_URL` (default: http://timestamp.digicert.com)

### macOS notarization
- Set: `RELEASE_NOTARIZE_MAC=1`
- Provide:
  - `MAC_SIGN_IDENTITY`
  - `MAC_BUNDLE_ID`
  - `MAC_NOTARY_PROFILE`

Example (macOS):
- `RELEASE_NOTARIZE_MAC=1 MAC_SIGN_IDENTITY="Developer ID Application: ..." MAC_BUNDLE_ID="com.cryptobotpro.desktop" MAC_NOTARY_PROFILE="NotaryProfile" python scripts/release_checklist.py --briefcase`

Example (Windows):
- `set RELEASE_SIGN_WINDOWS=1`
- `set SIGN_PFX_PATH=C:\path\cert.pfx`
- `set SIGN_PFX_PASSWORD=...`
- `python scripts/release_checklist.py --pyinstaller`

