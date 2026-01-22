#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo "ERROR: .venv not found. Run installers/install.sh first."
  exit 2
fi

source ".venv/bin/activate"
python -m pip install -U pip
python -m pip install -r requirements/dev.txt
python scripts/pre_release_sanity.py
