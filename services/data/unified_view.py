from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from storage.market_store_sqlite import MarketStore

def mid_from_ticker(t: Dict[str, Any]) -> Optional[float]:
    bid = t.get("bid")
    ask = t.get("ask")
    last = t.get("last")
    if bid is not None and ask is not None and (float(bid) + float(ask)) > 0:
        return (float(bid) + float(ask)) / 2.0
    if last is not None:
        return float(last)
    return None

def latest_mid_by_exchange(*, store: MarketStore, exchanges: List[str], symbol: str, limit: int = 2) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for ex in exchanges:
        rows = store.last_tickers(exchange=ex, symbol=symbol, limit=limit)
        if not rows:
            out[ex] = {"mid": None, "ts_ms": None}
            continue
        m = mid_from_ticker(rows[0])
        out[ex] = {"mid": m, "ts_ms": rows[0].get("ts_ms"), "bid": rows[0].get("bid"), "ask": rows[0].get("ask"), "last": rows[0].get("last")}
    return out

def cross_exchange_spread_bps(*, mids: Dict[str, Any]) -> Optional[float]:
    vals = [v.get("mid") for v in mids.values() if v.get("mid") is not None]
    if len(vals) < 2:
        return None
    hi = max(vals); lo = min(vals)
    mid = (hi + lo) / 2.0
    if mid <= 0: return None
    return (hi - lo) / mid * 10000.0
