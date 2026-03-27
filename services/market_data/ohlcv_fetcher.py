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
    since_ms: int | None = None


def fetch_ohlcv(
    venue: str,
    canonical_symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
) -> list[list]:
    return _fetch_ohlcv(
        str(venue),
        str(canonical_symbol),
        timeframe=str(timeframe),
        limit=int(limit),
        since_ms=None if since_ms is None else int(since_ms),
    )


def fetch(req: OHLCVFetchRequest) -> dict[str, Any]:
    rows = fetch_ohlcv(req.venue, req.symbol, timeframe=req.timeframe, limit=req.limit, since_ms=req.since_ms)
    return {
        "ok": True,
        "venue": str(req.venue),
        "symbol": str(req.symbol),
        "timeframe": str(req.timeframe),
        "limit": int(req.limit),
        "since_ms": None if req.since_ms is None else int(req.since_ms),
        "rows": rows,
        "count": len(rows),
    }


def load_ohlcv(
    venue: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
) -> list[list]:
    # Compatibility alias for older imports.
    return fetch_ohlcv(venue, symbol, timeframe=timeframe, limit=limit, since_ms=since_ms)
