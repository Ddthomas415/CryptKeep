#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
ASSET="${1:-SOL}"
QUESTION="${2:-Why is ${ASSET} moving?}"

RESPONSE="$(
  curl -fsS "${BASE_URL}/query/explain" \
    -H "content-type: application/json" \
    -d "{\"asset\":\"${ASSET}\",\"question\":\"${QUESTION}\"}"
)"

export RESPONSE_JSON="${RESPONSE}"
python - <<'PY'
import json
import os
import sys

required = [
    "asset",
    "question",
    "current_cause",
    "past_precedent",
    "future_catalyst",
    "confidence",
    "evidence",
    "execution_disabled",
]
payload = json.loads(os.environ["RESPONSE_JSON"])
missing = [k for k in required if k not in payload]
if missing:
    raise SystemExit(f"missing_keys:{','.join(missing)}")
if payload["execution_disabled"] is not True:
    raise SystemExit("execution_disabled must be true in Phase 1")
print(json.dumps(payload, indent=2))
sys.exit(0)
PY

echo "smoke_explain_ok"
