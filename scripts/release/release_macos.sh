#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Required on macOS: Xcode Command Line Tools (xcrun, notarytool, stapler)

bash scripts/validate.sh


VER="$(cat VERSION 2>/dev/null || echo "0.0.0")"
echo "[release] version: $VER"


# Build .app and DMG (unsigned by default)
bash packaging/macos/build_app_and_dmg.sh

APP="dist/CryptoBotPro.app"
DMG="dist_dmg/CryptoBotPro.dmg"

# Optional: codesign
if [[ -n "${MAC_DEVELOPER_ID_APP:-}" ]]; then
  echo "[release] codesign: $APP"
  codesign --force --deep --options runtime --timestamp -s "$MAC_DEVELOPER_ID_APP" "$APP"
  codesign --verify --deep --strict --verbose=2 "$APP"
else
  echo "[release] SKIP codesign (set MAC_DEVELOPER_ID_APP)"
fi

# Optional: notarize DMG and staple tickets
if [[ -n "${MAC_NOTARY_PROFILE:-}" ]]; then
  echo "[release] notarize: $DMG (profile: $MAC_NOTARY_PROFILE)"
  xcrun notarytool submit "$DMG" --keychain-profile "$MAC_NOTARY_PROFILE" --wait

  echo "[release] staple: $APP"
  xcrun stapler staple "$APP"

  echo "[release] staple: $DMG"
  xcrun stapler staple "$DMG"
else
  echo "[release] SKIP notarize/staple (set MAC_NOTARY_PROFILE)"
fi

echo "[release] DONE: $DMG"
