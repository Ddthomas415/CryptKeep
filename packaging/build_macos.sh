#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

"$PY" -m pip install --upgrade pip
if [ -f "requirements-dev.txt" ]; then
  "$PY" -m pip install -r requirements-dev.txt
else
  "$PY" -m pip install -r requirements.txt
fi

"$PY" packaging/pyinstaller/build.py

echo ""
echo "Build complete."
echo "Output: dist/CryptoBotPro (set CBP_WINDOWED=1 to produce dist/CryptoBotPro.app on macOS)."
