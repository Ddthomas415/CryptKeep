#!/bin/bash
set -euo pipefail

DIST_DIR="${1:-dist}"
APP_NAME="${2:-CryptoBotPro}"

# Required secrets (base64 P12 + password + notarization creds)
req() { [[ -n "${!1:-}" ]] || { echo "SKIP: $1 not set"; exit 0; }; }

req MAC_SIGN_P12_B64
req MAC_SIGN_P12_PASSWORD
req APPLE_ID
req APPLE_APP_PASSWORD
req APPLE_TEAM_ID

APP_PATH="${DIST_DIR}/${APP_NAME}.app"
if [[ ! -d "$APP_PATH" ]]; then
  echo "ERROR: app not found: $APP_PATH"
  exit 1
fi

# Create temporary keychain
KEYCHAIN_PATH="$RUNNER_TEMP/cbp-signing.keychain-db"
KEYCHAIN_PW="temp_pw_$(date +%s)"

security create-keychain -p "$KEYCHAIN_PW" "$KEYCHAIN_PATH"
security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
security unlock-keychain -p "$KEYCHAIN_PW" "$KEYCHAIN_PATH"

# Decode cert
P12_PATH="$RUNNER_TEMP/cbp_sign.p12"
echo "$MAC_SIGN_P12_B64" | base64 --decode > "$P12_PATH"

# Import cert
security import "$P12_PATH" -k "$KEYCHAIN_PATH" -P "$MAC_SIGN_P12_PASSWORD" -T /usr/bin/codesign -T /usr/bin/security

# Make keychain available
security list-keychains -d user -s "$KEYCHAIN_PATH"
security default-keychain -s "$KEYCHAIN_PATH"

# Discover signing identity
IDENTITY="${MAC_SIGN_IDENTITY:-}"
if [[ -z "$IDENTITY" ]]; then
  IDENTITY=$(security find-identity -p codesigning -v "$KEYCHAIN_PATH" | head -n 1 | awk -F\" '{print $2}')
fi
if [[ -z "$IDENTITY" ]]; then
  echo "ERROR: no codesigning identity found in keychain."
  exit 1
fi

echo "Using identity: $IDENTITY"

# Codesign (deep)
codesign --force --deep --options runtime --sign "$IDENTITY" "$APP_PATH"
codesign --verify --deep --strict --verbose=2 "$APP_PATH"

# Notarize + staple
xcrun notarytool submit "$APP_PATH" \
  --apple-id "$APPLE_ID" \
  --password "$APPLE_APP_PASSWORD" \
  --team-id "$APPLE_TEAM_ID" \
  --wait

xcrun stapler staple "$APP_PATH"
echo "DONE: macOS sign + notarize + staple complete."
