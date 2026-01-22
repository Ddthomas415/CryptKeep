# create_market_quality_guard.py - Creates missing Phase 114 file
from pathlib import Path

def create_file():
    path = Path("services/risk/market_quality_guard.py")
    path.parent.mkdir(parents=True, exist_ok=True)

    content = r'''from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional
from services.admin.config_editor import load_user_yaml
from services.market_data.tick_reader import get_best_bid_ask_last

def _cfg() -> dict:
    cfg = load_user_yaml()
    g = cfg.get("market_quality_guard") if isinstance(cfg.get("market_quality_guard"), dict) else {}
    return {
        "enabled": bool(g.get("enabled", True)),
        "max_tick_age_sec": float(g.get("max_tick_age_sec", 3.0) or 3.0),
        "max_spread_bps": float(g.get("max_spread_bps", 80.0) or 80.0),
        "require_bid_ask": bool(g.get("require_bid_ask", True)),
        "block_when_unknown": bool(g.get("block_when_unknown", True)),
    }

def check(venue: str, symbol: str) -> dict:
    cfg = _cfg()
    if not cfg["enabled"]:
        return {"ok": True, "enabled": False}
    q = get_best_bid_ask_last(venue, symbol)
    if not q:
        return {"ok": (not cfg["block_when_unknown"]), "reason": "no_quote"}
    ts_ms = int(q.get("ts_ms") or 0)
    age = 9999.0
    if ts_ms > 0:
        age = (time.time() * 1000.0 - float(ts_ms)) / 1000.0
    bid = q.get("bid")
    ask = q.get("ask")
    last = q.get("last")
    if cfg["require_bid_ask"] and (bid is None or ask is None):
        return {"ok": (not cfg["block_when_unknown"]), "reason": "missing_bid_ask", "age_sec": age, "bid": bid, "ask": ask, "last": last}
    spread_bps = _compute_spread_bps(bid, ask, last)
    if age > cfg["max_tick_age_sec"]:
        return {"ok": False, "reason": "stale_tick", "age_sec": age, "spread_bps": spread_bps}
    if spread_bps is None:
        return {"ok": (not cfg["block_when_unknown"]), "reason": "unknown_spread", "age_sec": age}
    if spread_bps > cfg["max_spread_bps"]:
        return {"ok": False, "reason": "spread_too_wide", "age_sec": age, "spread_bps": spread_bps}
    return {"ok": True, "age_sec": age, "spread_bps": spread_bps, "bid": bid, "ask": ask, "last": last}

def _compute_spread_bps(bid, ask, last=None):
    try:
        if bid is None or ask is None:
            return None
        b = float(bid)
        a = float(ask)
        if b <= 0 or a <= 0:
            return None
        mid = (a + b) / 2.0
        if mid <= 0:
            return None
        return ((a - b) / mid) * 10000.0
    except Exception:
        return None
'''

    path.write_text(content, encoding="utf-8")
    print(f"Created missing file: {path}")
    print("Now you can run:")
    print("  python3 scripts/run_live_intent_consumer.py run")

if __name__ == "__main__":
    create_file()