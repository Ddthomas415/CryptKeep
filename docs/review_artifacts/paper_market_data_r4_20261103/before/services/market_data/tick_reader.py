from __future__ import annotations
import json
from typing import Optional, Tuple
from services.os.app_paths import runtime_dir

LATEST = runtime_dir() / "snapshots" / "system_status.latest.json"


def _from_ticks_snapshot(snap: dict, venue: str, symbol: str) -> Optional[dict]:
    ticks = snap.get("ticks") if isinstance(snap, dict) else None
    if not isinstance(ticks, list):
        return None
    v = str(venue).lower().strip()
    s = str(symbol).strip()
    best = None
    for t in ticks:
        if not isinstance(t, dict):
            continue
        if str(t.get("venue", "")).lower().strip() == v and str(t.get("symbol", "")).strip() == s:
            best = t
    if not best:
        return None
    return {
        "ts_ms": int(best.get("ts_ms") or 0),
        "bid": best.get("bid"),
        "ask": best.get("ask"),
        "last": best.get("last"),
    }


def _from_venues_snapshot(snap: dict, venue: str) -> Optional[dict]:
    venues = snap.get("venues") if isinstance(snap, dict) else None
    if not isinstance(venues, dict):
        return None
    row = venues.get(str(venue).lower().strip())
    if not isinstance(row, dict):
        return None
    return {
        "ts_ms": int(snap.get("ts_ms") or row.get("timestamp") or 0),
        "bid": row.get("bid"),
        "ask": row.get("ask"),
        "last": row.get("last"),
    }

def get_best_bid_ask_last(venue: str, symbol: str) -> Optional[dict]:
    try:
        if not LATEST.exists():
            return None
        snap = json.loads(LATEST.read_text(encoding="utf-8"))
        best = _from_ticks_snapshot(snap, venue, symbol)
        if best is not None:
            return best
        return _from_venues_snapshot(snap, venue)
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
