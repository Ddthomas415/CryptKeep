from __future__ import annotations
import time
from typing import List, Optional
from services.market_data.symbol_router import normalize_venue, normalize_symbol, map_symbol
from services.market_data.tick_reader import get_best_bid_ask_last
from services.risk.market_quality_guard import check as mq_check

def _age_sec(ts_ms: int | None) -> float | None:
    try:
        if not ts_ms:
            return None
        return (time.time() * 1000.0 - float(ts_ms)) / 1000.0
    except Exception:
        return None

def venue_rows(venues: List[str], canonical_symbol: str) -> list[dict]:
    sym = normalize_symbol(canonical_symbol)
    out = []
    for v0 in venues:
        v = normalize_venue(v0)
        mapped = map_symbol(v, sym)
        q = get_best_bid_ask_last(v, sym)
        bid = q.get("bid") if q else None
        ask = q.get("ask") if q else None
        last = q.get("last") if q else None
        ts_ms = int(q.get("ts_ms") or 0) if q else 0
        age = _age_sec(ts_ms) if ts_ms else None
        spread_bps = _compute_spread_bps(bid, ask, last)
        guard = mq_check(v, sym)
        out.append({
            "venue": v,
            "canonical_symbol": sym,
            "mapped_symbol": mapped,
            "bid": bid,
            "ask": ask,
            "last": last,
            "ts_ms": ts_ms if ts_ms else None,
            "age_sec": age,
            "spread_bps": spread_bps,
            "guard_ok": bool(guard.get("ok")),
            "guard_reason": guard.get("reason"),
        })
    return out

def rank_rows(rows: list[dict]) -> list[dict]:
    def key(r: dict):
        ok = 0 if r.get("guard_ok") else 1
        age = r.get("age_sec")
        spread = r.get("spread_bps")
        age_key = float(age) if age is not None else 1e9
        spread_key = float(spread) if spread is not None else 1e9
        return (ok, age_key, spread_key, str(r.get("venue") or ""))
    return sorted(rows, key=key)

def best_venue(venues: List[str], canonical_symbol: str, *, require_ok: bool = True) -> dict | None:
    rows = rank_rows(venue_rows(venues, canonical_symbol))
    if not rows:
        return None
    if require_ok:
        for r in rows:
            if r.get("guard_ok"):
                return r
        return None
    return rows[0]
