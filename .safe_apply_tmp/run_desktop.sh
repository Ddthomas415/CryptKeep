#!/usr/bin/env bash
set -euo pipefail
[ -x ".venv/bin/python" ] || { echo "ERROR: .venv missing — run python3 scripts/install.py"; exit 1; }
.venv/bin/python -m cbp_desktop.launcher
