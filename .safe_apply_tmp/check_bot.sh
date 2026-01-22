#!/usr/bin/env bash
echo "=== Crypto Bot Pro Health Check ==="
echo "Date: $(date)"
echo ""

# 1. Kill local dashboard on 8501
echo "Port 8501 check..."
if lsof -i :8501 > /dev/null 2>&1; then
  PID=$(lsof -t -i :8501)
  echo "Killing local dashboard PID $PID..."
  kill -9 $PID 2>/dev/null || true
else
  echo "Port 8501 free"
fi

# 2. Start tick publisher if not running
echo ""
echo "=== Tick Publisher ==="
if pgrep -f "run_tick_publisher.py" > /dev/null; then
  echo "Already running"
else
  echo "Starting tick publisher..."
  nohup python3 scripts/run_tick_publisher.py run > runtime/logs/tick_publisher.log 2>&1 &
  echo "Started (wait 60s for snapshot...)"
  sleep 60
fi

# 3. Show latest snapshot prices
echo ""
echo "=== Snapshot Prices (last known) ==="
if [[ -f runtime/snapshots/system_status.latest.json ]]; then
  python3 - << 'END_PY'
import json
from pathlib import Path
f = Path("runtime/snapshots/system_status.latest.json")
if f.exists():
    data = json.loads(f.read_text())
    venues = data.get("venues", {})
    print(f"Snapshot ts: {data.get('ts', 'missing')}")
    for v in ["binance", "coinbase", "gateio"]:
        vd = venues.get(v, {})
        ok = vd.get("ok", False)
        bid = vd.get("bid", "no_bid")
        ask = vd.get("ask", "no_ask")
        last = vd.get("last", "no_last")
        reason = vd.get("reason", "ok") if not ok else ""
        print(f"{v}: ok={ok}, bid={bid}, ask={ask}, last={last} {reason}")
else:
    print("No snapshot file yet")
END_PY
else
  echo "No snapshot file yet"
fi

# 4. Preflight check
echo ""
echo "=== Preflight ==="
python3 scripts/run_preflight.py

# 5. Consumer status
echo ""
echo "=== Live Consumer Status ==="
cat runtime/flags/live_consumer.status.json 2>/dev/null || echo "No status file"

# 6. Log tails
echo ""
echo "=== Tick Publisher Log Tail (last 10 lines) ==="
tail -n 10 runtime/logs/tick_publisher.log 2>/dev/null || echo "No log"

echo ""
echo "=== Live Consumer Log Tail (last 10 lines) ==="
tail -n 10 runtime/logs/live_consumer.log 2>/dev/null || echo "No log"

# 7. Launch dashboard if not running
echo ""
echo "=== Dashboard ==="
if lsof -i :8501 > /dev/null 2>&1; then
  echo "Dashboard already running on port 8501"
else
  echo "Launching dashboard..."
  nohup streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0 > runtime/logs/dashboard.log 2>&1 &
  echo "Dashboard started. Open http://localhost:8501"
fi

echo ""
echo "All checks done. Run './check_bot.sh' anytime."
