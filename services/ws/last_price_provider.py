# Phase 187: Unified last-price provider (WS + fallback polling)
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from services.market_data.tick_reader import get_best_bid_ask_last, mid_price


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_last_price(
    *,
    venue: str,
    symbol: str,
    max_age_ms: int = 5_000,
    allow_stale: bool = False,
) -> Dict[str, Any]:
    q = get_best_bid_ask_last(str(venue), str(symbol))
    if not q:
        return {"ok": False, "reason": "no_quote", "venue": str(venue), "symbol": str(symbol)}
    ts_ms = int(q.get("ts_ms") or 0)
    age = (_now_ms() - ts_ms) if ts_ms > 0 else 10**9
    if not allow_stale and age > int(max_age_ms):
        return {"ok": False, "reason": "stale_quote", "venue": str(venue), "symbol": str(symbol), "age_ms": int(age)}
    px = mid_price(q)
    if px is None:
        return {"ok": False, "reason": "no_mid", "venue": str(venue), "symbol": str(symbol), "quote": q}
    return {"ok": True, "venue": str(venue), "symbol": str(symbol), "price": float(px), "age_ms": int(age), "quote": q}
