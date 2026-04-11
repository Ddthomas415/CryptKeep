from __future__ import annotations

import math
import time
from typing import Any

try:
    import ccxt
except Exception:
    ccxt = None


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def _sum_notional(levels: list[list[Any]] | None, depth: int) -> float:
    total = 0.0
    for row in list(levels or [])[:depth]:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        px = _safe_float(row[0], 0.0)
        sz = _safe_float(row[1], 0.0)
        if px > 0 and sz > 0:
            total += px * sz
    return total


def get_order_book_snapshot(
    *,
    symbol: str,
    venue: str = "coinbase",
    depth: int = 10,
) -> dict[str, Any]:
    if ccxt is None:
        return {"ok": False, "reason": "ccxt_unavailable"}

    ex_cls = getattr(ccxt, venue, None)
    if ex_cls is None:
        return {"ok": False, "reason": f"unknown_venue:{venue}"}

    ex = ex_cls({"enableRateLimit": True})
    try:
        ob = ex.fetch_order_book(symbol, limit=max(depth, 10))
        bids = list(ob.get("bids") or [])
        asks = list(ob.get("asks") or [])

        bid_notional = _sum_notional(bids, depth)
        ask_notional = _sum_notional(asks, depth)
        total = bid_notional + ask_notional

        imbalance = ((bid_notional - ask_notional) / total) if total > 1e-12 else 0.0
        pressure = "balanced"
        if imbalance >= 0.15:
            pressure = "buy_pressure"
        elif imbalance <= -0.15:
            pressure = "sell_pressure"

        best_bid = _safe_float(bids[0][0], 0.0) if bids else 0.0
        best_ask = _safe_float(asks[0][0], 0.0) if asks else 0.0
        spread_pct = ((best_ask - best_bid) / best_bid * 100.0) if best_bid > 0 and best_ask > 0 else 0.0

        return {
            "ok": True,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "venue": venue,
            "symbol": symbol,
            "depth": depth,
            "best_bid": round(best_bid, 8),
            "best_ask": round(best_ask, 8),
            "spread_pct": round(spread_pct, 4),
            "bid_notional": round(bid_notional, 2),
            "ask_notional": round(ask_notional, 2),
            "imbalance": round(imbalance, 4),
            "pressure": pressure,
        }
    finally:
        try:
            ex.close()
        except Exception:
            pass


def scan_order_book_pressure(
    *,
    symbols: list[str] | None = None,
    venue: str = "coinbase",
    depth: int = 10,
) -> dict[str, Any]:
    target = symbols or ["BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD", "LINK/USD"]
    rows = []
    for symbol in target:
        row = get_order_book_snapshot(symbol=symbol, venue=venue, depth=depth)
        if row.get("ok"):
            rows.append(row)

    rows.sort(key=lambda r: abs(_safe_float(r.get("imbalance"), 0.0)), reverse=True)

    return {
        "ok": True,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "venue": venue,
        "rows": rows,
        "buy_pressure": [r for r in rows if r.get("pressure") == "buy_pressure"],
        "sell_pressure": [r for r in rows if r.get("pressure") == "sell_pressure"],
    }
