#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

alembic upgrade head
python scripts/seed_assets.py
python scripts/seed_sources.py

echo "Bootstrap complete."
