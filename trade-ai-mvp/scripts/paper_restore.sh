#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <backup.sql>"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  # shellcheck disable=SC1091
  source ".env"
fi

POSTGRES_USER="${POSTGRES_USER:-trade_ai}"
POSTGRES_DB="${POSTGRES_DB:-trade_ai}"
IN_FILE="$1"

if [[ ! -f "$IN_FILE" ]]; then
  echo "backup file not found: $IN_FILE"
  exit 1
fi

cat "$IN_FILE" | docker compose exec -T postgres psql \
  -v ON_ERROR_STOP=1 \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB"

echo "paper restore completed from: $IN_FILE"
