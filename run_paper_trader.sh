#!/usr/bin/env bash
set -euo pipefail
if [ ! -x ".venv/bin/python" ]; then
  echo "ERROR: .venv not found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
mkdir -p data
.venv/bin/python -m services.paper_trader.main
