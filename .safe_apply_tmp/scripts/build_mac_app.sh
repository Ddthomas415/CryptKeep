#!/usr/bin/env bash
set -euo pipefail

# Build a macOS app bundle via PyInstaller (run on macOS)
# Requirements:
#   python -m pip install pyinstaller
#
# Build:
#   bash scripts/build_mac_app.sh

python3 -m pip install --upgrade pyinstaller
pyinstaller --noconfirm packaging/pyinstaller/crypto_bot_pro.spec

echo "OK: Build finished."
echo "Output: dist/CryptoBotPro/CryptoBotPro"
