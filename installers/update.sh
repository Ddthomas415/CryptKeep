#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source ".venv/bin/activate"

REQ=""
if [ -f "requirements.txt" ]; then
  REQ="requirements.txt"
elif [ -f "requirements/base.txt" ]; then
  REQ="requirements/base.txt"
fi

if [ -n "$REQ" ]; then
  python -m pip install --upgrade -r "$REQ"
  echo "[CryptoBotPro] Updated dependencies from $REQ"
else
  echo "WARNING: No requirements file found."
fi
