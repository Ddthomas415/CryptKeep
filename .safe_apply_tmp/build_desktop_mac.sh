#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 scripts/bootstrap.py install
./.venv/bin/python -m pip install --upgrade pyinstaller pywebview
./.venv/bin/python scripts/build_desktop.py
echo "DONE. See dist_desktop/"
