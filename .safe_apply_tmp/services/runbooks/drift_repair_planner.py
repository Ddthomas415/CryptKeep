from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List

def now_ms() -> int:
    return int(time.time() * 1000)

@dataclass(frozen=True)
class RepairPolicy:
    allowed_actions: List[str]
    default_actions: List[str]
    max_flatten_symbols: int = 0

def _hash(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def build_repair_plan_from_drift(exchange: str, drift: Dict[str, Any], policy: RepairPolicy) -> Dict[str, Any]:
    actions: List[Dict[str, Any]] = []
    summary_parts: List[str] = []

    if "CANCEL_OPEN_ORDERS" in policy.allowed_actions and "CANCEL_OPEN_ORDERS" in policy.default_actions:
        actions.append({"type": "CANCEL_OPEN_ORDERS", "params": {"exchange": exchange}})
        summary_parts.append("cancel open orders")

    # Cash drift: sync primary cash only (internal ledger)
    cash = (drift.get("cash") or {}).get("primary") or {}
    if cash.get("abs_drift", 0) and "SYNC_CASH" in policy.allowed_actions:
        actions.append({"type": "SYNC_CASH", "params": {"exchange": exchange, "quote_ccy": cash.get("quote_ccy")}})
        summary_parts.append("sync cash")

    # Position drifts: require exchange_symbol explicitly
    pos = drift.get("positions") or []
    for p in pos:
        if p.get("abs_drift", 0) and "SYNC_POSITION" in policy.allowed_actions:
            actions.append({
                "type": "SYNC_POSITION",
                "params": {
                    "exchange": exchange,
                    "canonical_symbol": p.get("canonical_symbol"),
                    "exchange_symbol": p.get("exchange_symbol"),
                    "base": p.get("base"),
                }
            })
            summary_parts.append(f"sync {p.get('canonical_symbol')}")

    plan = {
        "plan_id": f"drift-{exchange}-{now_ms()}",
        "exchange": exchange,
        "summary": ", ".join(summary_parts) if summary_parts else "no-op",
        "actions": actions,
        "meta": {"source": "drift_repair_planner", "note": "SYNC_POSITION requires exchange_symbol; no guessing"},
    }
    plan["plan_hash"] = _hash(plan)
    return plan
