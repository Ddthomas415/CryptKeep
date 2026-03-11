#!/usr/bin/env bash
set -euo pipefail

APP_DIR="dist/CryptoBotPro"
APP_NAME="CryptoBotPro.app"
DMG_NAME="CryptoBotPro.dmg"

echo "This helper assumes you built a macOS .app bundle."
echo "If you used --onedir --console, you'll have a folder not a .app yet."
echo "To build a .app, you typically use PyInstaller --windowed on macOS. (See docs/PACKAGING.md)"

if [[ ! -d "$APP_DIR/$APP_NAME" ]]; then
  echo "ERROR: Not found: $APP_DIR/$APP_NAME"
  exit 2
fi

rm -f "$DMG_NAME"
hdiutil create -volname "CryptoBotPro" -srcfolder "$APP_DIR/$APP_NAME" -ov -format UDZO "$DMG_NAME"
echo "OK: $DMG_NAME created."
