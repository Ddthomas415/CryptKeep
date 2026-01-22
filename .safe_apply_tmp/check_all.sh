#!/usr/bin/env bash
set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

issues=()

echo -e "${GREEN}=== Crypto Bot Pro Health Check ===${NC}"
echo "Date: $(date)"
echo ""

# ── 1. Port 8501 check & kill ────────────────────────────────────────────────
echo -n "Port 8501: "
if lsof -i :8501 >/dev/null 2>&1; then
  PID=$(lsof -t -i :8501)
  echo -n "Killing PID $PID... "
  kill -9 "$PID" 2>/dev/null && echo -e "${GREEN}OK${NC}" || {
    echo -e "${RED}FAILED${NC}"
    issues+=("Port 8501 kill failed (PID $PID)")
  }
else
  echo -e "${GREEN}free${NC}"
fi

# ── 2. Tick publisher ────────────────────────────────────────────────────────
echo ""
echo "=== Tick Publisher ==="
if pgrep -f "run_tick_publisher.py" >/dev/null; then
  echo -e "${GREEN}Running${NC}"
else
  echo "Starting..."
  nohup python3 scripts/run_tick_publisher.py run > runtime/logs/tick_publisher.log 2>&1 &
  echo "Started — waiting 60s..."
  sleep 60
fi

# ── 3. Snapshot prices ───────────────────────────────────────────────────────
echo ""
echo "=== Snapshot Prices ==="
snapshot_ok=false
if [[ -f runtime/snapshots/system_status.latest.json ]]; then
  python3 - << 'END_PY'
import json, pathlib
f = pathlib.Path("runtime/snapshots/system_status.latest.json")
if f.exists() and f.stat().st_size > 0:
    d = json.loads(f.read_text())
    print(f"ts: {d.get('ts', 'missing')}")
    v = d.get("venues", {})
    for name in ["binance", "coinbase", "gateio"]:
        vd = v.get(name, {})
        ok = vd.get("ok", False)
        bid = vd.get("bid", "no_bid")
        ask = vd.get("ask", "no_ask")
        last = vd.get("last", "no_last")
        reason = vd.get("reason", "") if not ok else ""
        print(f"{name:9} ok={ok}, bid={bid}, ask={ask}, last={last} {reason}")
    if any(v.get("ok", False) for v in v.values()):
        print("At least one good venue")
END_PY
  snapshot_ok=true
else
  echo -e "${RED}No snapshot file yet${NC}"
  issues+=("No snapshot file")
fi

# ── 4. Preflight ──────────────────────────────────────────────────────────────
echo ""
echo "=== Preflight ==="
preflight_ok=false
python3 scripts/run_preflight.py > /tmp/preflight.out 2>&1
cat /tmp/preflight.out | grep -E "ready|problems|market_quality|live_arming"
if grep -q '"ready": true' /tmp/preflight.out; then
  echo -e "${GREEN}Preflight: READY${NC}"
  preflight_ok=true
else
  echo -e "${RED}Preflight: NOT READY${NC}"
  grep "problems" /tmp/preflight.out >> /tmp/issues.txt
  issues+=("Preflight not ready")
fi

# ── 5. Consumer status ────────────────────────────────────────────────────────
echo ""
echo "=== Live Consumer Status ==="
consumer_ok=false
if [[ -f runtime/flags/live_consumer.status.json ]]; then
  cat runtime/flags/live_consumer.status.json
  if grep -q '"status": "running"' runtime/flags/live_consumer.status.json; then
    echo -e "${GREEN}Consumer running${NC}"
    consumer_ok=true
  else
    echo -e "${RED}Consumer blocked or stopped${NC}"
    grep "reason" runtime/flags/live_consumer.status.json >> /tmp/issues.txt
    issues+=("Consumer not running")
  fi
else
  echo -e "${RED}No consumer status file${NC}"
  issues+=("No consumer status file")
fi

# ── 6. Log tails ──────────────────────────────────────────────────────────────
echo ""
echo "=== Tick Publisher Log Tail (last 15 lines) ==="
tail -n 15 runtime/logs/tick_publisher.log 2>/dev/null || echo "No log"

echo ""
echo "=== Live Consumer Log Tail (last 15 lines) ==="
tail -n 15 runtime/logs/live_consumer.log 2>/dev/null || echo "No log"

# ── 7. Dashboard check & start ────────────────────────────────────────────────
echo ""
echo "=== Dashboard ==="
if lsof -i :8501 >/dev/null 2>&1; then
  PID=$(lsof -t -i :8501)
  echo -e "${GREEN}Running (PID $PID) → http://localhost:8501${NC}"
else
  echo "Starting..."
  nohup streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0 > runtime/logs/dashboard.log 2>&1 &
  DASH_PID=$!
  echo -e "${GREEN}Started (PID $DASH_PID) — open http://localhost:8501${NC}"
fi

# ── Summary of Issues ─────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}=== SUMMARY OF ISSUES ===${NC}"
if [ ${#issues[@]} -eq 0 ]; then
  echo -e "${GREEN}All checks passed!${NC}"
else
  echo -e "${RED}Issues found:${NC}"
  for issue in "${issues[@]}"; do
    echo " - $issue"
  done
fi

echo ""
echo "Run './check_all.sh' anytime."
