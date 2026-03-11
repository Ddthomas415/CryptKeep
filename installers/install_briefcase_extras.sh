#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

"$PY" -m pip install --upgrade pip
"$PY" scripts/sync_briefcase_requires.py
"$PY" -m pip install briefcase
"$PY" -m pip install -r requirements/briefcase.txt

echo "Done: briefcase extras installed."
