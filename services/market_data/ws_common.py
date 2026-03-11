# Phase 176: Coinbase + Gate.io WS adapters
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def normalize_ws_symbol(symbol: str) -> str:
    s = str(symbol or "").strip().upper().replace("_", "/").replace("-", "/")
    if "/" in s:
        a, b = s.split("/", 1)
        return f"{a}/{b}"
    return s


def normalize_ticker_message(msg: Dict[str, Any], *, venue: str, symbol: str | None = None) -> Dict[str, Any]:
    m = dict(msg or {})
    sym = str(symbol or m.get("symbol") or m.get("product_id") or "")
    bid = m.get("bid") if m.get("bid") is not None else m.get("best_bid")
    ask = m.get("ask") if m.get("ask") is not None else m.get("best_ask")
    last = m.get("last") if m.get("last") is not None else m.get("price")
    ts = m.get("ts_ms") or m.get("timestamp") or now_ms()
    try:
        ts_ms = int(ts)
    except Exception:
        ts_ms = now_ms()
    return {
        "venue": str(venue).lower().strip(),
        "symbol": normalize_ws_symbol(sym),
        "ts_ms": ts_ms,
        "bid": (None if bid is None else float(bid)),
        "ask": (None if ask is None else float(ask)),
        "last": (None if last is None else float(last)),
        "raw": m,
    }
