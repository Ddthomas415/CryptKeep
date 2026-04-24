#!/usr/bin/env bash
set -euo pipefail

# Build a macOS app bundle via PyInstaller (run on macOS)
# Requirements:
#   python -m pip install pyinstaller
#
# Build:
#   bash scripts/build_mac_app.sh

bash scripts/build_macos.sh

echo "OK: Build finished."
echo "Output: dist/CryptoBotPro.app"
