#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller

# Build (macOS .app bundle can be created with --windowed; we keep console for logs)
pyinstaller -y packaging/pyinstaller/crypto_bot_pro.spec

echo "DONE: dist/CryptoBotPro/ (run dist/CryptoBotPro/CryptoBotPro)"
