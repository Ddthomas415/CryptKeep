#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ "$(uname -s)" != "Darwin" ]; then
  echo "ERROR: packaging/pyinstaller/build_macos.sh must run on macOS."
  exit 1
fi

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements/desktop.txt

CBP_WINDOWED=1 "$PY" packaging/pyinstaller/build.py

echo "DONE: dist/CryptoBotPro.app"
