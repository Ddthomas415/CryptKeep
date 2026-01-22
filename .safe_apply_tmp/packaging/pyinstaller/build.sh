#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo "ERROR: .venv not found. Run installers/install.sh first."
  exit 1
fi

source ".venv/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r requirements/desktop.txt

pyinstaller --noconfirm --clean \
  --name CryptoBotPro \
  --onefile \
  --hidden-import streamlit \
  --hidden-import webview \
  packaging/desktop_wrapper.py

echo "Built: dist/CryptoBotPro"
