#!/usr/bin/env bash
set -euo pipefail
[ -x ".venv/bin/python" ] || { echo "ERROR: .venv missing — run python3 scripts/install.py"; exit 1; }
export CBP_TRADER_WEBHOOK_HOST="${CBP_TRADER_WEBHOOK_HOST:-127.0.0.1}"
export CBP_TRADER_WEBHOOK_PORT="${CBP_TRADER_WEBHOOK_PORT:-8787}"
.venv/bin/python -m services.trader_signals.webhook_server
