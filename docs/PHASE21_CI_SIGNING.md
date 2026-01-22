# Phase 21 — CI Signing + CI Notarization (optional)

## Why gated
If secrets are missing, CI must still build + publish unsigned artifacts.
GitHub recommends mapping secrets to env vars and using env-based `if:` gating. :contentReference[oaicite:3]{index=3}

## Windows signing (signtool)
- Uses scripts/ci/windows_sign.ps1
- Requires:
  - WIN_CERT_PFX_B64  (base64 .pfx)
  - WIN_CERT_PASSWORD
  - optional WIN_TIMESTAMP_URL
- signtool signs and can timestamp/verify. :contentReference[oaicite:4]{index=4}

## macOS signing + notarization (notarytool + stapler)
- Uses scripts/ci/macos_sign_notarize.sh
- Signing requires:
  - MAC_CERT_P12_B64, MAC_CERT_PASSWORD, MAC_SIGN_IDENTITY
- Notarization supports:
  A) App Store Connect API key:
     - MAC_NOTARY_KEY_P8_B64, MAC_NOTARY_KEY_ID, MAC_NOTARY_ISSUER
  B) Apple ID app-specific password:
     - MAC_APPLE_ID, MAC_APPLE_PW, MAC_TEAM_ID

notarytool supports submit auth by API key (-k/-d/-i) or Apple ID (--apple-id/--password/--team-id). :contentReference[oaicite:5]{index=5}
Apple describes notarytool + stapler as the standard workflow. :contentReference[oaicite:6]{index=6}

## Where configured
- .github/workflows/publish_release.yml
