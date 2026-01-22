# Phase 308 — CI Signing (Windows) + CI Notarization (macOS)

Workflow:
- `.github/workflows/ci-signing.yml` (manual trigger)

## Windows signing (signtool action)
Secrets required (repo/org secrets):
- `WIN_CERTIFICATE_BASE64`  (base64 of your .pfx)
- `WIN_CERT_PASSWORD`
- One of:
  - `WIN_CERT_SHA1` (thumbprint)
  - `WIN_CERT_NAME` (subject name)

The workflow signs everything under `dist/` recursively.

## macOS notarization (notarytool)
Secrets required:
- `MAC_APPLE_ID`
- `MAC_APP_PASSWORD` (app-specific password)
- `MAC_TEAM_ID`

It creates a keychain profile (`NotaryProfile`) then submits DMG(s) and staples them.

References:
- notarytool supports `store-credentials` and `submit --wait` with keychain profiles. :contentReference[oaicite:2]{index=2}
- Windows SignTool requires specifying digest algorithms (/fd and /td) and supports signing/timestamping. :contentReference[oaicite:3]{index=3}
- GitHub Marketplace Windows signtool action (base64 PFX + password + sha1/name). :contentReference[oaicite:4]{index=4}

## macOS code-signing (Phase 309)
Additional secrets (for codesign in CI):
- `MAC_CERT_P12_BASE64` (base64 of Developer ID Application .p12)
- `MAC_CERT_PASSWORD`
- `MAC_KEYCHAIN_PASSWORD` (password for temp CI keychain)
- `MAC_SIGN_IDENTITY` (e.g., "Developer ID Application: Your Company (TEAMID)")

Flow:
- Import P12 into a temporary keychain
- Codesign any .app bundles under build/ and dist/
- Then notarize DMG(s) (Phase 308)

## Phase 310 verification
After signing/notarization, CI performs verification:

### Windows
- `signtool verify /pa /v` against all `.exe/.msi` under `dist/`

### macOS
- `xcrun stapler validate -v` on DMG(s)
- `spctl --assess --type execute --verbose=2` on `.app` bundles (if present)

## Phase 311 final distributable hash manifest
After signing/notarization, CI runs:
- `python scripts/release_checklist.py`

This writes `releases/release_manifest_*.json` capturing SHA-256 hashes for final artifacts in `dist/` and `build/`.

