#!/usr/bin/env bash
set -euo pipefail

# Inputs via env (recommended):
# Signing:
# - MAC_CERT_P12_B64       (base64 of Developer ID Application .p12)
# - MAC_CERT_PASSWORD
# - MAC_SIGN_IDENTITY      (e.g. "Developer ID Application: Your Name (TEAMID)")
#
# Notarization (choose ONE auth method):
# A) App Store Connect API key (recommended for CI):
# - MAC_NOTARY_KEY_P8_B64  (base64 of AuthKey_XXXX.p8)
# - MAC_NOTARY_KEY_ID      (10-char key id)
# - MAC_NOTARY_ISSUER      (issuer UUID)  [Team key]
#
# B) Apple ID + app-specific password:
# - MAC_APPLE_ID
# - MAC_APPLE_PW
# - MAC_TEAM_ID
#
# Artifacts:
APP="dist/CryptoBotPro.app"
DMG="dist_dmg/CryptoBotPro.dmg"

if [[ -z "${MAC_CERT_P12_B64:-}" || -z "${MAC_CERT_PASSWORD:-}" || -z "${MAC_SIGN_IDENTITY:-}" ]]; then
  echo "SKIP: missing MAC_CERT_P12_B64 / MAC_CERT_PASSWORD / MAC_SIGN_IDENTITY"
  exit 0
fi

if [[ ! -d "$APP" ]]; then
  echo "ERROR: app not found: $APP"
  exit 2
fi

# Create a temp keychain for CI
KEYCHAIN="$RUNNER_TEMP/cbp-signing.keychain-db"
KEYCHAIN_PW="temp_pw_$(date +%s)"

security create-keychain -p "$KEYCHAIN_PW" "$KEYCHAIN"
security set-keychain-settings -lut 21600 "$KEYCHAIN"
security unlock-keychain -p "$KEYCHAIN_PW" "$KEYCHAIN"
security list-keychains -d user -s "$KEYCHAIN"
security default-keychain -s "$KEYCHAIN"

# Import cert
P12="$RUNNER_TEMP/cbp_cert.p12"
echo "$MAC_CERT_P12_B64" | base64 --decode > "$P12"
security import "$P12" -k "$KEYCHAIN" -P "$MAC_CERT_PASSWORD" -T /usr/bin/codesign -T /usr/bin/security

# Allow codesign without UI prompts
security set-key-partition-list -S apple-tool:,apple: -s -k "$KEYCHAIN_PW" "$KEYCHAIN" >/dev/null

echo "codesign: $APP"
codesign --force --deep --options runtime --timestamp -s "$MAC_SIGN_IDENTITY" "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

# Notarize DMG (notarytool submit supports API key or Apple ID flows) :contentReference[oaicite:1]{index=1}
if [[ -f "$DMG" ]]; then
  if [[ -n "${MAC_NOTARY_KEY_P8_B64:-}" && -n "${MAC_NOTARY_KEY_ID:-}" && -n "${MAC_NOTARY_ISSUER:-}" ]]; then
    KEY="$RUNNER_TEMP/AuthKey_${MAC_NOTARY_KEY_ID}.p8"
    echo "$MAC_NOTARY_KEY_P8_B64" | base64 --decode > "$KEY"
    echo "notarytool submit (API key): $DMG"
    xcrun notarytool submit "$DMG" --key "$KEY" --key-id "$MAC_NOTARY_KEY_ID" --issuer "$MAC_NOTARY_ISSUER" --wait
  elif [[ -n "${MAC_APPLE_ID:-}" && -n "${MAC_APPLE_PW:-}" && -n "${MAC_TEAM_ID:-}" ]]; then
    echo "notarytool submit (Apple ID): $DMG"
    xcrun notarytool submit "$DMG" --apple-id "$MAC_APPLE_ID" --password "$MAC_APPLE_PW" --team-id "$MAC_TEAM_ID" --wait
  else
    echo "SKIP notarization: missing notary credentials"
    exit 0
  fi

  echo "stapler staple app + dmg"
  xcrun stapler staple "$APP"
  xcrun stapler staple "$DMG"
else
  echo "SKIP notarization: dmg not found: $DMG"
fi

echo "DONE: signed (and notarized if creds provided)"
