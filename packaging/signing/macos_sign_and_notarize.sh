#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash packaging/signing/macos_sign_and_notarize.sh \
#     --app "dist/CryptoBotPro.app" \
#     --identity "Developer ID Application: Your Company (TEAMID)" \
#     --bundle-id "com.cryptobotpro.desktop" \
#     --notary-profile "YourNotaryProfile"

APP=""
IDENTITY=""
BUNDLE_ID=""
NOTARY_PROFILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app) APP="$2"; shift 2;;
    --identity) IDENTITY="$2"; shift 2;;
    --bundle-id) BUNDLE_ID="$2"; shift 2;;
    --notary-profile) NOTARY_PROFILE="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

if [[ -z "$APP" || -z "$IDENTITY" || -z "$BUNDLE_ID" || -z "$NOTARY_PROFILE" ]]; then
  echo "Missing args."
  exit 2
fi

if [[ ! -d "$APP" ]]; then
  echo "App not found: $APP"
  exit 2
fi

echo "[macOS] codesign (deep + hardened runtime)..."
codesign --force --options runtime --timestamp --deep --sign "$IDENTITY" "$APP"

echo "[macOS] verify codesign..."
codesign --verify --deep --strict --verbose=2 "$APP"

echo "[macOS] create notarization zip (ditto keep parent)..."
ZIP="${APP%.app}.zip"
rm -f "$ZIP"
ditto -c -k --keepParent "$APP" "$ZIP"

echo "[macOS] submit to notarization (notarytool)..."
xcrun notarytool submit "$ZIP" --keychain-profile "$NOTARY_PROFILE" --wait

echo "[macOS] staple ticket..."
xcrun stapler staple "$APP"

echo "[macOS] assess gatekeeper..."
spctl --assess --type execute --verbose=2 "$APP"

echo "[macOS] done. Stapled app: $APP"
