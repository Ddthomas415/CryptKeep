from __future__ import annotations
import time
from typing import Dict, Any, Optional
from services.admin.config_editor import load_user_yaml
from services.market_data.tick_reader import get_best_bid_ask_last


def _cfg() -> Dict[str, Any]:
    cfg = load_user_yaml()
    g = cfg.get("market_quality_guard", {})
    return {
        "enabled": bool(g.get("enabled", True)),
        "max_tick_age_sec": float(g.get("max_tick_age_sec", 600.0)),   # 10 min
        "max_spread_bps": float(g.get("max_spread_bps", 500.0)),       # 5%
        "require_bid_ask": False,
        "block_when_unknown": False,
    }


def check(venue: str, symbol: str) -> Dict[str, Any]:
    cfg = _cfg()
    if not cfg["enabled"]:
        return {"ok": True, "reason": "guard_disabled"}

    q = get_best_bid_ask_last(venue, symbol)
    if not q:
        return {"ok": True, "reason": "no_quote_data"}

    ts_ms = int(q.get("ts_ms") or 0)
    age_sec = 9999.0
    if ts_ms > 0:
        age_sec = (time.time() * 1000.0 - float(ts_ms)) / 1000.0

    bid = q.get("bid")
    ask = q.get("ask")
    last = q.get("last")

    price = last
    if bid is not None and ask is not None:
        price = (float(bid) + float(ask)) / 2.0

    if price is None or price <= 0:
        return {"ok": True, "reason": "no_usable_price"}

    spread_bps = None
    if bid is not None and ask is not None:
        try:
            spread_bps = ((float(ask) - float(bid)) / float(bid)) * 10000.0
            if spread_bps > cfg["max_spread_bps"]:
                return {"ok": False, "reason": "spread_too_wide"}
        except:
            pass

    if ts_ms > 0 and age_sec > cfg["max_tick_age_sec"]:
        return {"ok": False, "reason": "stale_tick", "age_sec": age_sec}

    return {
        "ok": True,
        "age_sec": age_sec if ts_ms > 0 else None,
        "spread_bps": spread_bps,
        "bid": bid,
        "ask": ask,
        "last": last,
        "price_used": price,
    }
