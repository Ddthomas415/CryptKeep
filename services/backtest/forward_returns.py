from __future__ import annotations

from typing import Any

from dashboard.services.view_data import _load_local_ohlcv


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def compute_forward_return_pct_from_ohlcv(
    *,
    venue: str,
    symbol: str,
    timeframe: str = "1h",
    entry_index: int = -2,
    forward_bars: int = 1,
    limit: int = 240,
) -> dict[str, Any]:
    rows = _load_local_ohlcv(venue, symbol, timeframe=timeframe, limit=limit) or []
    if not rows or len(rows) < abs(entry_index) + forward_bars + 1:
        return {
            "ok": False,
            "reason": "insufficient_ohlcv",
            "return_pct": 0.0,
        }

    closes = [_safe_float(r[4], 0.0) for r in rows if isinstance(r, (list, tuple)) and len(r) >= 5]
    if len(closes) < abs(entry_index) + forward_bars + 1:
        return {
            "ok": False,
            "reason": "insufficient_closes",
            "return_pct": 0.0,
        }

    n = len(closes)
    entry_pos = n + entry_index if entry_index < 0 else entry_index
    exit_pos = entry_pos + forward_bars

    if entry_pos < 0 or exit_pos >= n:
        return {
            "ok": False,
            "reason": "index_out_of_range",
            "return_pct": 0.0,
        }

    entry_px = _safe_float(closes[entry_pos], 0.0)
    exit_px = _safe_float(closes[exit_pos], 0.0)
    if entry_px <= 0 or exit_px <= 0:
        return {
            "ok": False,
            "reason": "invalid_prices",
            "return_pct": 0.0,
        }

    ret = ((exit_px - entry_px) / entry_px) * 100.0
    return {
        "ok": True,
        "entry_price": round(entry_px, 8),
        "exit_price": round(exit_px, 8),
        "return_pct": round(ret, 4),
        "forward_bars": int(forward_bars),
        "timeframe": timeframe,
    }
