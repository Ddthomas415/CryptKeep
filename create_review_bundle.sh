#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-.}"
OUTDIR="${2:-$PWD}"

if [[ ! -d "$SRC" ]]; then
  echo "Source directory not found: $SRC"
  exit 1
fi

NAME="$(basename "$(cd "$SRC" && pwd)")"
STAMP="$(date +"%Y%m%d_%H%M%S")"
TMPDIR="$(mktemp -d)"
BUNDLE_DIR="$TMPDIR/${NAME}_review_bundle"
ZIP_PATH="$OUTDIR/${NAME}_review_bundle_${STAMP}.zip"

mkdir -p "$BUNDLE_DIR"

rsync -a \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.mypy_cache' \
  --exclude '.ruff_cache' \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude 'build' \
  --exclude '*.log' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude '*.sqlite' \
  --exclude '*.db' \
  --exclude '.coverage' \
  --exclude 'htmlcov' \
  "$SRC/" "$BUNDLE_DIR/"

cat > "$BUNDLE_DIR/REVIEW_BUNDLE_NOTES.txt" <<'EOF'
Review bundle generated for repo sharing.

Excluded:
- .git
- virtualenvs
- caches
- node_modules
- logs
- .env files
- local DB files

Recommended review entry points:
- README.md
- dashboard/
- phase1_research_copilot/
- attic/trade-ai-mvp/
- tools/
- tests/
EOF

(
  cd "$TMPDIR"
  zip -r "$ZIP_PATH" "$(basename "$BUNDLE_DIR")" >/dev/null
)

rm -rf "$TMPDIR"

echo "Created:"
echo "$ZIP_PATH"
