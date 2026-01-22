# App Branding + Signing Notes

## Icons
Place icons here:
- `assets/icon/app.ico` (Windows)
- `assets/icon/app.icns` (macOS)

The build script will use them automatically if present.

## Versioning
Edit:
- `desktop_app/app_meta.json` → `version`, `bundle_id`, names

## Signing readiness (later)
- Windows: you’ll want to code-sign the .exe to reduce SmartScreen warnings.
- macOS: you’ll want to sign + notarize the .app for smoother first-run experience (Gatekeeper).
This phase only prepares identifiers/metadata; it does not sign anything.
