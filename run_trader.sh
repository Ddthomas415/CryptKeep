#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
if [ ! -d ".venv" ]; then
  echo "ERROR: .venv not found. Run installer first."
  exit 2
fi
source ".venv/bin/activate"
python -m services.trading_runner.run_trader --config config/trading.yaml
