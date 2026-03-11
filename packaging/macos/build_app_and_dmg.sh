#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ "$(uname -s)" != "Darwin" ]; then
  echo "ERROR: packaging/macos/build_app_and_dmg.sh must run on macOS."
  exit 1
fi

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

"$PY" -m pip install --upgrade pip
if [ -f "requirements-packaging.txt" ]; then
  "$PY" -m pip install -r requirements-packaging.txt
else
  "$PY" -m pip install -r requirements.txt
fi

# Build .app (windowed)
CBP_WINDOWED=1 "$PY" packaging/pyinstaller/build.py

APP="dist/CryptoBotPro.app"
if [ ! -d "$APP" ]; then
  echo "ERROR: expected app bundle not found: $APP"
  exit 1
fi

# Create DMG (unsigned by default)
mkdir -p dist_dmg
DMG="dist_dmg/CryptoBotPro.dmg"
rm -f "$DMG"

# Apple's tooling supports DMG creation with hdiutil
# Example pattern: hdiutil create -format UDZO -srcfolder <folder> <dmg>
hdiutil create -format UDZO -srcfolder "$APP" "$DMG"

echo "DONE: $DMG"
echo "NOTE: For distribution outside your machine, you likely need codesign + notarization."
