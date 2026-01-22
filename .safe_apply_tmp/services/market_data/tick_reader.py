from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Tuple
from services.os.app_paths import runtime_dir

LATEST = runtime_dir() / "snapshots" / "system_status.latest.json"

def get_best_bid_ask_last(venue: str, symbol: str) -> Optional[dict]:
    try:
        if not LATEST.exists():
            return None
        snap = json.loads(LATEST.read_text(encoding="utf-8"))
        ticks = snap.get("ticks") if isinstance(snap, dict) else None
        if not isinstance(ticks, list):
            return None
        v = str(venue).lower().strip()
        s = str(symbol).strip()
        # pick the most recent matching tick
        best = None
        for t in ticks:
            if not isinstance(t, dict):
                continue
            if str(t.get("venue","")).lower().strip() == v and str(t.get("symbol","")).strip() == s:
                best = t
        if not best:
            return None
        return {
            "ts_ms": int(best.get("ts_ms") or 0),
            "bid": best.get("bid"),
            "ask": best.get("ask"),
            "last": best.get("last"),
        }
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
