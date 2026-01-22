#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   curl -fsSL <URL>/install.sh | bash
# or (local repo)
#   bash scripts/install.sh

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
REQ="${REQ:-requirements.txt}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3.11+ then re-run."
  exit 2
fi

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel setuptools

if [ -f "$REQ" ]; then
  pip install -r "$REQ"
else
  echo "ERROR: requirements.txt not found"
  exit 3
fi

echo "OK: Installed. Launching desktop runner..."
python scripts/run_desktop.py
