#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

if [ -f "requirements/desktop.txt" ]; then
  "$PY" -m pip install -r requirements/desktop.txt
else
  "$PY" -m pip install -r requirements.txt
fi

"$PY" packaging/pyinstaller/build.py

echo "Built: dist/CryptoBotPro (set CBP_WINDOWED=1 for a macOS .app build)"
