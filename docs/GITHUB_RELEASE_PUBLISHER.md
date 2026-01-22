# Phase 312 — GitHub Release Publisher

Workflow:
- `.github/workflows/release-publish.yml`

Triggers:
- Tag push: `v*` (e.g. `v0.1.0`)
- Manual: workflow_dispatch (optional inputs)

What it does:
- Builds Windows + macOS artifacts
- Optional signing/notarization if secrets are present (workflow skips those steps otherwise)
- Writes final `releases/release_manifest_*.json` after any signing/notary
- Publishes/updates a GitHub Release and attaches build outputs + manifests

Required:
- None (build + attach works without signing secrets)

Optional secrets:
- Windows signing:
  - WIN_CERTIFICATE_BASE64, WIN_CERT_PASSWORD, (WIN_CERT_SHA1 or WIN_CERT_NAME)
- macOS codesign/notary:
  - MAC_CERT_P12_BASE64, MAC_CERT_PASSWORD, MAC_KEYCHAIN_PASSWORD, MAC_SIGN_IDENTITY
  - MAC_APPLE_ID, MAC_APP_PASSWORD, MAC_TEAM_ID
