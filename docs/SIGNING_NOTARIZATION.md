# Signing + Notarization (Optional, CI)

Nothing in this repo signs by default. Signing steps run ONLY if secrets are present.

## Windows (Authenticode)
GitHub Secrets:
- `WIN_SIGN_PFX_B64` : base64 of your .pfx signing cert
- `WIN_SIGN_PFX_PASSWORD` : password for that .pfx
- `WIN_SIGN_TIMESTAMP_URL` : optional (defaults in script)

Notes:
- The workflow calls: `scripts/ci/sign_windows.ps1`
- It signs the `.exe` under `dist/CryptoBotPro/*.exe` and verifies.

## macOS (codesign + notarize + staple)
GitHub Secrets:
- `MAC_SIGN_P12_B64` : base64 of Developer ID Application certificate (.p12)
- `MAC_SIGN_P12_PASSWORD` : password for that .p12
- `MAC_SIGN_IDENTITY` : optional. If omitted, script uses first identity in keychain.
- `APPLE_ID` : Apple ID for notarization
- `APPLE_APP_PASSWORD` : app-specific password
- `APPLE_TEAM_ID` : your team id

Notes:
- The workflow calls: `scripts/ci/sign_macos.sh`
- It codesigns with hardened runtime and submits to notarization via `notarytool`, then staples.

## How to base64 encode cert files
- macOS/Linux:
  - `base64 -i cert.p12 | pbcopy` (mac) / `base64 cert.p12 > cert.b64`
- Windows (PowerShell):
  - `[Convert]::ToBase64String([IO.File]::ReadAllBytes("cert.pfx"))`
