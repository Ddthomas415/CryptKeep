from __future__ import annotations
import json
from typing import Optional, Tuple
from services.os.app_paths import runtime_dir
from services.market_data.symbol_router import normalize_symbol

LATEST = runtime_dir() / "snapshots" / "system_status.latest.json"


def _from_ticks_snapshot(snap: dict, venue: str, symbol: str) -> Optional[dict]:
    ticks = snap.get("ticks") if isinstance(snap, dict) else None
    if not isinstance(ticks, list):
        return None
    v = str(venue).lower().strip()
    # Same spelling rule the publisher writes ticks with (case, dash or slash).
    s = normalize_symbol(str(symbol))
    best = None
    for t in ticks:
        if not isinstance(t, dict):
            continue
        if str(t.get("venue", "")).lower().strip() == v and normalize_symbol(str(t.get("symbol", ""))) == s:
            best = t
    if not best:
        return None
    return {
        "ts_ms": int(best.get("ts_ms") or 0),
        "bid": best.get("bid"),
        "ask": best.get("ask"),
        "last": best.get("last"),
    }


def get_best_bid_ask_last(venue: str, symbol: str) -> Optional[dict]:
    """Latest snapshot quote for exactly this venue and symbol, or None.

    The snapshot's venue-level row is the quote of whichever symbol was
    fetched first for that venue. It is never returned here: a symbol with no
    tick of its own has no quote.
    """
    try:
        if not LATEST.exists():
            return None
        snap = json.loads(LATEST.read_text(encoding="utf-8"))
        return _from_ticks_snapshot(snap, venue, symbol)
    except Exception:
        return None

def mid_price(q: dict) -> Optional[float]:
    try:
        b = q.get("bid")
        a = q.get("ask")
        if b is None or a is None:
            l = q.get("last")
            return float(l) if l is not None else None
        return (float(b) + float(a)) / 2.0
    except Exception:
        return None
