#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller

# Build .app
pyinstaller -y packaging/pyinstaller/crypto_bot_pro_macos.spec

# Create DMG (unsigned by default)
mkdir -p dist_dmg
DMG="dist_dmg/CryptoBotPro.dmg"
rm -f "$DMG"

# Apple's tooling supports DMG creation with hdiutil
# Example pattern: hdiutil create -format UDZO -srcfolder <folder> <dmg>
hdiutil create -format UDZO -srcfolder "dist/CryptoBotPro.app" "$DMG"

echo "DONE: $DMG"
echo "NOTE: For distribution outside your machine, you likely need codesign + notarization."
