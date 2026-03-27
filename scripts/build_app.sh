#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

"$PY" -m pip install --upgrade pip
if [ -f "requirements/desktop.txt" ]; then
  "$PY" -m pip install -r requirements/desktop.txt
elif [ -f "requirements.txt" ]; then
  "$PY" -m pip install -r requirements.txt
else
  "$PY" -m pip install pyinstaller
fi

"$PY" packaging/pyinstaller/build.py
echo "DONE. Output is in dist/ (set CBP_WINDOWED=1 for a macOS .app build)."
