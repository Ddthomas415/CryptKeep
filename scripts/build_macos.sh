#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$(uname -s)" != "Darwin" ]; then
  echo "ERROR: scripts/build_macos.sh must run on macOS."
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

CBP_WINDOWED=1 "$PY" packaging/pyinstaller/build.py

APP_PATH="dist/CryptoBotPro.app"
if [ ! -d "$APP_PATH" ]; then
  echo "ERROR: expected app bundle not found: $APP_PATH"
  exit 1
fi

echo ""
echo "DONE (macOS): $APP_PATH"
echo ""
