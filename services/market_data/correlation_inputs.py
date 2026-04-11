from __future__ import annotations

from typing import Any

from dashboard.services.view_data import _load_local_ohlcv


def load_series_by_symbol(
    *,
    venue: str,
    symbols: list[str],
    timeframe: str = "1h",
    limit: int = 120,
) -> dict[str, list[list[Any]]]:
    out: dict[str, list[list[Any]]] = {}
    for symbol in symbols:
        sym = str(symbol or "").strip()
        if not sym:
            continue
        try:
            rows = _load_local_ohlcv(venue, sym, timeframe=timeframe, limit=limit) or []
            if rows:
                out[sym] = rows
        except Exception:
            continue
    return out
