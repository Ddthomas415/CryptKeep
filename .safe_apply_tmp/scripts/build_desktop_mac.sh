#!/usr/bin/env bash
set -euo pipefail

# Build macOS app/executable locally (must run on macOS)
# Output: dist/CryptoBotPro (or dist/CryptoBotPro.app later if we wrap)
# This uses your system python; recommended: python3 -m venv .venv

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"

# BUILD_APP=1 builds a real .app bundle (no console).
# ICON (optional): packaging/icons/CryptoBotPro.icns
BUILD_APP="${BUILD_APP:-0}"
ICON_PATH="packaging/icons/CryptoBotPro.icns"

if [ ! -d ".venv" ]; then
  $PY -m venv .venv
fi
source .venv/bin/activate

python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt
python -m pip install pyinstaller

if [ "$BUILD_APP" = "1" ]; then
  if [ -f "$ICON_PATH" ]; then
    pyinstaller --noconfirm --icon "$ICON_PATH" packaging/pyinstaller/crypto_bot_pro_app.spec
  else
    pyinstaller --noconfirm packaging/pyinstaller/crypto_bot_pro_app.spec
  fi
  echo ""
  echo "Built: $ROOT/dist/CryptoBotPro.app"
  echo "Run:   open $ROOT/dist/CryptoBotPro.app"
else
  pyinstaller --noconfirm packaging/pyinstaller/crypto_bot_pro.spec
  echo ""
  echo "Built: $ROOT/dist/CryptoBotPro"
  echo "Run:   ./dist/CryptoBotPro"
fi

echo ""
echo "Built: $ROOT/dist/CryptoBotPro"
echo "Run:   ./dist/CryptoBotPro"
