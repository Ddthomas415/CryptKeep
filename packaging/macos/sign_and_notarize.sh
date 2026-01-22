#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   export MAC_SIGN_ID="Developer ID Application: Your Name (TEAMID)"
#   export MAC_BUNDLE_ID="com.yourcompany.cryptobotpro"
#   export APPLE_ID="you@example.com"
#   export TEAM_ID="TEAMID"
#   export APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
#
#   bash packaging/macos/sign_and_notarize.sh dist/CryptoBotProDesktop/CryptoBotProDesktop

APP_BIN="${1:-dist/CryptoBotProDesktop/CryptoBotProDesktop}"
if [[ ! -f "$APP_BIN" ]]; then
  echo "Missing binary: $APP_BIN"
  exit 2
fi

if [[ -z "${MAC_SIGN_ID:-}" ]]; then
  echo "Set MAC_SIGN_ID (Developer ID Application...)"
  exit 3
fi

echo "[1/4] codesign binary (and embedded libs, if any)"
codesign --force --options runtime --timestamp --sign "$MAC_SIGN_ID" "$APP_BIN"

echo "[2/4] verify signature"
codesign --verify --deep --strict --verbose=2 "$APP_BIN"

echo "[3/4] create zip for notarization upload"
ZIP_OUT="dist/CryptoBotProDesktop-macos.zip"
ditto -c -k --sequesterRsrc --keepParent "$(dirname "$APP_BIN")" "$ZIP_OUT"

echo "[4/4] submit to notarization (notarytool) and staple ticket"
if [[ -z "${APPLE_ID:-}" || -z "${TEAM_ID:-}" || -z "${APP_SPECIFIC_PASSWORD:-}" ]]; then
  echo "Missing APPLE_ID / TEAM_ID / APP_SPECIFIC_PASSWORD (needed for notarytool)."
  echo "You can still distribute unsigned for local use, but Gatekeeper warnings are expected."
  exit 4
fi

xcrun notarytool submit "$ZIP_OUT" --apple-id "$APPLE_ID" --team-id "$TEAM_ID" --password "$APP_SPECIFIC_PASSWORD" --wait
# If distributing a .app or pkg, you'd staple to that artifact. Here we staple to folder/binary path.
xcrun stapler staple "$(dirname "$APP_BIN")" || true

echo "OK: signed + notarized attempt complete."
