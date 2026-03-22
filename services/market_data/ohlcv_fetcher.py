from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.backtest.signal_replay import fetch_ohlcv as _fetch_ohlcv


@dataclass(frozen=True)
class OHLCVFetchRequest:
    venue: str
    symbol: str
    timeframe: str = "1h"
    limit: int = 500


def fetch_ohlcv(venue: str, canonical_symbol: str, timeframe: str = "1h", limit: int = 500) -> list[list]:
    return _fetch_ohlcv(str(venue), str(canonical_symbol), timeframe=str(timeframe), limit=int(limit))


def fetch(req: OHLCVFetchRequest) -> dict[str, Any]:
    rows = fetch_ohlcv(req.venue, req.symbol, timeframe=req.timeframe, limit=req.limit)
    return {
        "ok": True,
        "venue": str(req.venue),
        "symbol": str(req.symbol),
        "timeframe": str(req.timeframe),
        "limit": int(req.limit),
        "rows": rows,
        "count": len(rows),
    }


def load_ohlcv(venue: str, symbol: str, timeframe: str = "1h", limit: int = 500) -> list[list]:
    # Compatibility alias for older imports.
    return fetch_ohlcv(venue, symbol, timeframe=timeframe, limit=limit)
