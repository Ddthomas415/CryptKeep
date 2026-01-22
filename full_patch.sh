#!/bin/bash
set -e

echo "🚀 Starting full clean + patch for crypto-bot..."

# ----------------------
# 1️⃣ Remove old execution files
# ----------------------
echo "🧹 Removing old execution files..."
rm -f services/execution/retry_policy.py
rm -f services/execution/order_router.py
rm -f services/execution/candle_checker.py

# ----------------------
# 2️⃣ Ensure execution directory exists
# ----------------------
mkdir -p services/execution

# ----------------------
# 3️⃣ Create retry_policy.py
# ----------------------
cat << 'EOF' > services/execution/retry_policy.py
from __future__ import annotations
import random, time

def _exc_name(e: Exception) -> str:
    return type(e).__name__

def is_retryable_exception(e: Exception) -> bool:
    name = _exc_name(e).lower()
    msg = str(e).lower()
    hard_no = [
        "insufficientfunds","invalidorder","badrequest","authenticationerror",
        "permissiondenied","account","ordernotfound","invalidnonce","argumentsrequired"
    ]
    if any(x in name for x in hard_no) or any(x in msg for x in hard_no):
        return False
    yes = [
        "ratelimitexceeded","requesttimeout","networkerror","exchangeerror",
        "exchangeunavailable","ddosprotection","temporary","timed out","timeout",
        "too many requests","429","503","502","504","connection reset","connection aborted"
    ]
    return any(x in name for x in yes) or any(x in msg for x in yes)

def backoff_sleep(attempt: int, base_delay_sec: float, max_delay_sec: float) -> float:
    a = max(0,int(attempt))
    base = max(0.05,float(base_delay_sec))
    cap = max(base,float(max_delay_sec))
    delay = min(cap, base*(2**a))
    jitter = random.uniform(0.0,min(0.25,delay*0.15))
    sleep_for = delay + jitter
    time.sleep(sleep_for)
    return float(sleep_for)
EOF

# ----------------------
# 4️⃣ Create order_router.py
# ----------------------
cat << 'EOF' > services/execution/order_router.py
from __future__ import annotations
from services.admin.config_editor import load_user_yaml
from services.security.exchange_factory import make_exchange
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from services.execution.retry_policy import is_retryable_exception, backoff_sleep
from storage.idempotency_sqlite import IdempotencySQLite

def _cfg() -> dict:
    cfg = load_user_yaml()
    lt = cfg.get("live_trading") or {}
    ex = lt.get("execution") or {}
    return {
        "max_order_retries": int(ex.get("max_order_retries",3)),
        "base_retry_delay_sec": float(ex.get("base_retry_delay_sec",0.6)),
        "max_retry_delay_sec": float(ex.get("max_retry_delay_sec",6.0)),
    }

def place_order_idempotent(*, venue, symbol, side, type, amount, price=None, idempotency_key, params=None, dry_run=True) -> dict:
    v = normalize_venue(venue)
    sym = normalize_symbol(symbol)
    side = str(side).lower().strip()
    type = str(type).lower().strip()
    params = params or {}
    idem = IdempotencySQLite()
    prior = idem.get(idempotency_key)
    if prior and prior.get("status") == "success":
        return {"ok": True, "idempotent": True, "result": prior.get("result"), "key": idempotency_key}
    if dry_run:
        result = {
            "dry_run": True, "venue": v, "symbol": sym,
            "side": side, "type": type, "amount": float(amount),
            "price": (float(price) if price else None), "params": params
        }
        idem.put_success(idempotency_key,result)
        return {"ok": True, "dry_run": True, "result": result, "_

