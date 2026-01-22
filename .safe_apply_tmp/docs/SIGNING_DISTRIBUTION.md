# Phase 305 — Signing & Distribution Hardening

## macOS (Developer ID + Notarization)
Apple’s recommended path for apps distributed outside the Mac App Store is:
1) Code sign with Developer ID and hardened runtime
2) Submit to Apple notarization service (notarytool)
3) Staple the notarization ticket (stapler)
4) Verify with Gatekeeper assessment (spctl)

References:
- Apple notarization overview (notarytool + stapler). :contentReference[oaicite:0]{index=0}
- Custom notarization workflow (xcrun notarytool submit …). :contentReference[oaicite:1]{index=1}
- Common notarization issues & troubleshooting. :contentReference[oaicite:2]{index=2}
- Developer ID / Gatekeeper signing overview. :contentReference[oaicite:3]{index=3}

### Script
- `packaging/signing/macos_sign_and_notarize.sh`

You must provide:
- `--identity` (Developer ID Application certificate name)
- `--notary-profile` (created via `xcrun notarytool store-credentials ...`)

---

## Windows (Authenticode + Timestamp)
Windows distribution best practice:
1) Sign the EXE with Authenticode
2) Timestamp the signature so it remains valid after cert expiration
3) Verify signature

References:
- Authenticode overview. :contentReference[oaicite:4]{index=4}
- SignTool documentation (sign / verify / timestamp). :contentReference[oaicite:5]{index=5}

### Script
- `packaging/signing/windows_sign.ps1`

You must provide either:
- A PFX file (+ password), OR
- A certificate thumbprint from the Windows cert store

---

## SmartScreen notes (Windows)
Even correctly signed apps can still show “not commonly downloaded” warnings until reputation is established; signing and reputation are related but not identical. :contentReference[oaicite:6]{index=6}
EV certificates can reduce friction in some cases, but it’s a business decision and not required for correctness. :contentReference[oaicite:7]{index=7}

---

## Where this integrates in our project
- Phase 300 install method remains the default (fast + reliable).
- Phase 301/302 packaging (PyInstaller/Briefcase) produces artifacts that can be signed using the scripts above.
- Phase 304 release_checklist generates manifests; signed artifacts should be included in `dist/` so hashes capture final signed output.

---

## Phase 306 integration (release_checklist hooks)
You can run signing/notarization as part of `python scripts/release_checklist.py` by setting:

- Windows: `RELEASE_SIGN_WINDOWS=1` + creds env vars
- macOS: `RELEASE_NOTARIZE_MAC=1` + identity/profile env vars

The script searches for artifacts under `dist/` and `build/` and fails closed if required env vars are missing.

