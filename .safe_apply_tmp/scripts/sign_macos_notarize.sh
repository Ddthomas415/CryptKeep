#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

APP="dist/CryptoBotPro.app"

# REQUIRED:
#  - Developer ID Application cert in Keychain (codesign will reference it)
#  - notarytool credentials saved as a keychain profile (Xcode tools): xcrun notarytool store-credentials ...
# See Apple notarization docs for notarytool + stapler usage. (Xcode command-line tools)  :contentReference[oaicite:3]{index=3}

SIGN_IDENTITY="${SIGN_IDENTITY:-Developer ID Application: YOUR NAME (TEAMID)}"
NOTARY_PROFILE="${NOTARY_PROFILE:-AC_NOTARY}"

if [ ! -d "$APP" ]; then
  echo "Missing $APP. Run: ./scripts/build_macos.sh"
  exit 2
fi

echo "==> codesign: $APP"
codesign --force --deep --options runtime --timestamp --sign "$SIGN_IDENTITY" "$APP"

echo "==> verify signature"
codesign --verify --deep --strict --verbose=2 "$APP"

echo "==> zip for notarization"
ZIP="dist/CryptoBotPro_notary.zip"
rm -f "$ZIP"
ditto -c -k --keepParent "$APP" "$ZIP"

echo "==> submit to notarization (wait)"
xcrun notarytool submit "$ZIP" --keychain-profile "$NOTARY_PROFILE" --wait

echo "==> staple"
xcrun stapler staple "$APP"

echo "==> done: notarized + stapled"
echo "APP: $APP"
