#!/bin/bash
set -e

# Run from repo root
cd "$(dirname "$0")/.."

# Ensure venv exists and deps installed
python3 -m installers.bootstrap venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -r requirements-dev.txt

# Build
./.venv/bin/pyinstaller --clean --noconfirm packaging/cryptobotpro.spec

echo ""
echo "Build complete."
echo "Output: dist/CryptoBotPro (macOS will produce an .app when using the windowed build; this spec uses console=True for safety)."
