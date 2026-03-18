from __future__ import annotations

from typing import Any, Dict, List


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def market_context(*, ohlcv: list, window: int = 8) -> Dict[str, float]:
    rows = [row for row in list(ohlcv or []) if isinstance(row, (list, tuple)) and len(row) >= 6]
    if not rows:
        return {
            "avg_range_pct": 0.0,
            "volume_ratio": 1.0,
            "trend_efficiency": 0.0,
            "prev_close": 0.0,
            "close": 0.0,
        }

    closes: List[float] = [_fnum(row[4], 0.0) for row in rows]
    highs: List[float] = [_fnum(row[2], 0.0) for row in rows]
    lows: List[float] = [_fnum(row[3], 0.0) for row in rows]
    volumes: List[float] = [_fnum(row[5], 0.0) for row in rows]

    n = max(2, min(int(window), len(rows)))
    close_slice = closes[-n:]
    high_slice = highs[-n:]
    low_slice = lows[-n:]
    volume_slice = volumes[-n:]

    range_pcts = []
    for high, low, close in zip(high_slice, low_slice, close_slice):
        base = max(abs(close), 1e-12)
        range_pcts.append(((high - low) / base) * 100.0)
    avg_range_pct = sum(range_pcts) / len(range_pcts) if range_pcts else 0.0

    baseline_volumes = volume_slice[:-1] or volume_slice
    volume_baseline = (sum(baseline_volumes) / len(baseline_volumes)) if baseline_volumes else 0.0
    volume_ratio = (volume_slice[-1] / volume_baseline) if volume_baseline > 1e-12 else 1.0

    path = 0.0
    for prev, cur in zip(close_slice[:-1], close_slice[1:]):
        path += abs(cur - prev)
    net = abs(close_slice[-1] - close_slice[0])
    trend_efficiency = (net / path) if path > 1e-12 else 0.0

    return {
        "avg_range_pct": float(avg_range_pct),
        "volume_ratio": float(volume_ratio),
        "trend_efficiency": float(trend_efficiency),
        "prev_close": float(close_slice[-2] if len(close_slice) >= 2 else close_slice[-1]),
        "close": float(close_slice[-1]),
    }


def pct_gap(a: float, b: float, *, base: float | None = None) -> float:
    denom = max(abs(float(base if base is not None else b)), 1e-12)
    return float((abs(float(a) - float(b)) / denom) * 100.0)
