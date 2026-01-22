#!/usr/bin/env bash
set -euo pipefail
if [ ! -x ".venv/bin/python" ]; then
  echo "ERROR: .venv not found. Run: python3 scripts/install.py"
  exit 1
fi
mkdir -p data
.venv/bin/python -m services.data_collector.main
