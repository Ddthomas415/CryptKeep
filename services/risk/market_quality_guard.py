from __future__ import annotations
import time
from typing import Dict, Any, Optional
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_symbol
from services.market_data.tick_reader import get_best_bid_ask_last


def _cfg() -> Dict[str, Any]:
    cfg = load_user_yaml()
    g = cfg.get("market_quality_guard", {}) if isinstance(cfg.get("market_quality_guard"), dict) else {}
    symbol_thresholds = g.get("symbol_thresholds") if isinstance(g.get("symbol_thresholds"), dict) else {}
    st_norm: Dict[str, Dict[str, float]] = {}
    for k, v in symbol_thresholds.items():
        if not isinstance(v, dict):
            continue
        sym = normalize_symbol(str(k))
        item: Dict[str, float] = {}
        if v.get("max_tick_age_sec") is not None:
            try:
                item["max_tick_age_sec"] = float(v.get("max_tick_age_sec"))
            except Exception:
                pass
        if v.get("max_spread_bps") is not None:
            try:
                item["max_spread_bps"] = float(v.get("max_spread_bps"))
            except Exception:
                pass
        if item:
            st_norm[sym] = item
    return {
        "enabled": bool(g.get("enabled", True)),
        "max_tick_age_sec": float(g.get("max_tick_age_sec", 600.0)),   # 10 min
        "max_spread_bps": float(g.get("max_spread_bps", 500.0)),       # 5%
        "require_bid_ask": bool(g.get("require_bid_ask", False)),
        "block_when_unknown": bool(g.get("block_when_unknown", False)),
        "symbol_thresholds": st_norm,
    }


def check(venue: str, symbol: str) -> Dict[str, Any]:
    cfg_base = _cfg()
    sym = normalize_symbol(symbol)
    cfg = dict(cfg_base)
    per = cfg_base.get("symbol_thresholds", {}).get(sym)
    if isinstance(per, dict):
        if per.get("max_tick_age_sec") is not None:
            cfg["max_tick_age_sec"] = float(per["max_tick_age_sec"])
        if per.get("max_spread_bps") is not None:
            cfg["max_spread_bps"] = float(per["max_spread_bps"])
    if not cfg["enabled"]:
        return {"ok": True, "reason": "guard_disabled"}

    q = get_best_bid_ask_last(venue, sym)
    if not q:
        if cfg["block_when_unknown"]:
            return {"ok": False, "reason": "no_quote_data"}
        return {"ok": True, "reason": "no_quote_data"}

    ts_ms = int(q.get("ts_ms") or 0)
    age_sec = 9999.0
    if ts_ms > 0:
        age_sec = (time.time() * 1000.0 - float(ts_ms)) / 1000.0

    bid = q.get("bid")
    ask = q.get("ask")
    last = q.get("last")

    if cfg["require_bid_ask"] and (bid is None or ask is None):
        return {"ok": False, "reason": "missing_bid_ask", "bid": bid, "ask": ask, "last": last}

    price = last
    if bid is not None and ask is not None:
        try:
            price = (float(bid) + float(ask)) / 2.0
        except Exception:
            if cfg["block_when_unknown"]:
                return {"ok": False, "reason": "invalid_bid_ask", "bid": bid, "ask": ask, "last": last}
            price = last

    if price is None or price <= 0:
        if cfg["block_when_unknown"]:
            return {"ok": False, "reason": "no_usable_price", "bid": bid, "ask": ask, "last": last}
        return {"ok": True, "reason": "no_usable_price"}

    spread_bps = None
    if bid is not None and ask is not None:
        try:
            spread_bps = ((float(ask) - float(bid)) / float(bid)) * 10000.0
            if spread_bps > cfg["max_spread_bps"]:
                return {"ok": False, "reason": "spread_too_wide"}
        except Exception:
            if cfg["block_when_unknown"]:
                return {"ok": False, "reason": "spread_calc_failed", "bid": bid, "ask": ask, "last": last}
            spread_bps = None

    if ts_ms > 0 and age_sec > cfg["max_tick_age_sec"]:
        return {"ok": False, "reason": "stale_tick", "age_sec": age_sec}

    return {
        "ok": True,
        "symbol": sym,
        "age_sec": age_sec if ts_ms > 0 else None,
        "spread_bps": spread_bps,
        "max_spread_bps": float(cfg["max_spread_bps"]),
        "max_tick_age_sec": float(cfg["max_tick_age_sec"]),
        "bid": bid,
        "ask": ask,
        "last": last,
        "price_used": price,
    }
