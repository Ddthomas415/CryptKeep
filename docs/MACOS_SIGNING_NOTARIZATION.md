# Phase 331 — macOS Signing + Notarization (Optional, Fail-Closed)

This project can ship unsigned DMGs, but macOS Gatekeeper will warn users.
Signing + notarization improves trust and reduces warnings.

## Local signing (optional)
Set:
- CODESIGN_IDENTITY="Developer ID Application: Your Company (TEAMID)"

Then:
- `bash scripts/build_macos_dmg.sh`

The build will:
- sign the `.app` if `CODESIGN_IDENTITY` is set

## Local notarization (optional)
Also set:
- APPLE_ID="you@example.com"
- APPLE_TEAM_ID="TEAMID"
- APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"   (App-specific password)

Then:
- `bash scripts/build_macos_dmg.sh`

The build will:
- submit DMG to Apple notary service
- staple the notarization ticket

## CI signing/notarization (optional)
Set GitHub Secrets (only if you want notarized releases):

Signing:
- MACOS_CERT_B64 : base64 of your Developer ID Application .p12
- MACOS_CERT_PASSWORD : password for the .p12
- CODESIGN_IDENTITY : exact identity string shown by `security find-identity -v -p codesigning`

Notarization:
- APPLE_ID
- APPLE_TEAM_ID
- APPLE_APP_PASSWORD

Fail-closed behavior:
- If secrets are not set, CI still builds and releases an unsigned DMG.
- If certificate is set but notarization secrets are missing, CI signs only.
