#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source ".venv/bin/activate"
python -m streamlit run dashboard/app.py --server.port 8501
