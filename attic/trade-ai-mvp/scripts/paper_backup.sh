#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  # shellcheck disable=SC1091
  source ".env"
fi

POSTGRES_USER="${POSTGRES_USER:-trade_ai}"
POSTGRES_DB="${POSTGRES_DB:-trade_ai}"
OUT_DIR="${1:-$ROOT_DIR/backups/paper}"
STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
OUT_FILE="$OUT_DIR/paper_tables_${STAMP}.sql"

mkdir -p "$OUT_DIR"

docker compose exec -T postgres pg_dump \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean \
  --if-exists \
  --table=paper_orders \
  --table=paper_fills \
  --table=paper_positions \
  --table=paper_balances \
  --table=paper_equity_curve \
  --table=paper_performance_rollups \
  > "$OUT_FILE"

echo "paper backup written: $OUT_FILE"
