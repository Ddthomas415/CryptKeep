# Phase 18 — Signing & notarization

## macOS (Developer ID + Notary)
Apple’s documented flow uses:
- `xcrun notarytool submit ... --wait`
- `xcrun stapler staple ...` :contentReference[oaicite:5]{index=5}

Environment vars used by `scripts/release_macos.sh`:
- MAC_DEVELOPER_ID_APP  (codesign identity for Developer ID Application)
- MAC_NOTARY_PROFILE    (name of a notarytool Keychain profile)

Typical setup outline:
1) Store credentials in Keychain (creates a profile)
2) Codesign the .app (hardened runtime + timestamp)
3) Notarize the DMG using notarytool
4) Staple tickets to the .app and the DMG

## Windows (SignTool)
Microsoft documents `signtool` for signing and timestamping. :contentReference[oaicite:6]{index=6}

Environment vars used by `scripts/release_windows.ps1`:
- SIGNTOOL_PATH (optional; auto-detected if Windows SDK is installed)
- WIN_CERT_PFX
- WIN_CERT_PASSWORD
- WIN_TIMESTAMP_URL (optional)

## Inno Setup signing integration
Inno Setup supports signing via a configured SignTool directive. :contentReference[oaicite:7]{index=7}
We currently sign in the release script (after PyInstaller build). If you want Inno to sign the installer automatically,
we can wire `SignTool=` inside the `.iss` later using your exact certificate workflow.
