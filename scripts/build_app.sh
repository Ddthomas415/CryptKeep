#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install -r requirements-dev.txt
python3 packaging/pyinstaller/build.py
echo "DONE. Run from dist/CryptoBotPro/ (or create installer next)."
