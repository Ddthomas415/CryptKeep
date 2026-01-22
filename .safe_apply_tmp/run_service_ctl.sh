#!/usr/bin/env bash
set -euo pipefail
if [ ! -x ".venv/bin/python" ]; then
  echo "ERROR: .venv not found. Run: python3 scripts/install.py"
  exit 1
fi
.venv/bin/python scripts/service_ctl.py "$@"
