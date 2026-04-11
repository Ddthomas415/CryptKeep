"""
Volume surge detection with historical baseline.

Compares current volume to a rolling baseline to detect
statistically unusual volume — not just a simple ratio.
"""
from __future__ import annotations
import math
from typing import Any


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else d
    except Exception:
        return d


def _stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = sum(values) / len(values)
    var = sum((x - mu) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(max(var, 0.0))


def detect_volume_surge(
    ohlcv: list,
    *,
    baseline_bars: int = 20,
    surge_z_score: float = 2.0,
    surge_ratio: float = 1.5,
) -> dict[str, Any]:
    """
    Detect statistically unusual volume using Z-score + ratio.

    A surge is flagged when BOTH:
    - current volume / baseline average >= surge_ratio
    - (current volume - mean) / stddev >= surge_z_score

    Returns:
        {
            "surge": bool,
            "ratio": float,
            "z_score": float,
            "current_vol": float,
            "baseline_avg": float,
            "baseline_std": float,
        }
    """
    if not ohlcv or len(ohlcv) < baseline_bars + 1:
        return {
            "surge":        False,
            "ratio":        1.0,
            "z_score":      0.0,
            "current_vol":  0.0,
            "baseline_avg": 0.0,
            "baseline_std": 0.0,
            "reason":       "insufficient_data",
        }

    volumes = [_safe(r[5]) for r in ohlcv if r and len(r) >= 6]
    current = volumes[-1]
    baseline = volumes[-(baseline_bars + 1):-1]

    avg = sum(baseline) / len(baseline) if baseline else 0.0
    std = _stddev(baseline)

    ratio   = (current / avg) if avg > 1e-10 else 1.0
    z_score = ((current - avg) / std) if std > 1e-10 else 0.0

    surge = ratio >= float(surge_ratio) and z_score >= float(surge_z_score)

    # Classify surge intensity
    if not surge:
        label = "normal"
    elif z_score >= 4.0:
        label = "extreme"
    elif z_score >= 3.0:
        label = "strong"
    else:
        label = "moderate"

    return {
        "surge":        surge,
        "label":        label,
        "ratio":        round(ratio, 2),
        "z_score":      round(z_score, 2),
        "current_vol":  round(current, 2),
        "baseline_avg": round(avg, 2),
        "baseline_std": round(std, 2),
    }


def detect_pump_pattern(
    ohlcv: list,
    *,
    min_move_pct: float = 5.0,
    min_bars: int = 3,
    max_bars: int = 12,
    volume_surge_ratio: float = 1.5,
) -> dict[str, Any]:
    """
    Detect pump/dump pattern: rapid price move with volume.

    Pump: price up >= min_move_pct in min_bars to max_bars with volume surge.
    Dump: price down >= min_move_pct in min_bars to max_bars with volume surge.
    """
    if not ohlcv or len(ohlcv) < max_bars + 2:
        return {"pump": False, "dump": False, "reason": "insufficient_data"}

    closes  = [_safe(r[4]) for r in ohlcv]
    cur     = closes[-1]

    # Check each window from min_bars to max_bars
    for n in range(int(min_bars), int(max_bars) + 1):
        start = closes[-(n + 1)]
        if start <= 0:
            continue
        move_pct = (cur - start) / start * 100.0

        vol_data = detect_volume_surge(ohlcv[-(n + 20):], surge_ratio=volume_surge_ratio)
        vol_confirmed = bool(vol_data.get("surge"))

        if move_pct >= float(min_move_pct) and vol_confirmed:
            return {
                "pump":       True,
                "dump":       False,
                "move_pct":   round(move_pct, 2),
                "bars":       n,
                "vol_ratio":  vol_data.get("ratio", 1.0),
                "vol_z":      vol_data.get("z_score", 0.0),
            }
        if move_pct <= -float(min_move_pct) and vol_confirmed:
            return {
                "pump":       False,
                "dump":       True,
                "move_pct":   round(move_pct, 2),
                "bars":       n,
                "vol_ratio":  vol_data.get("ratio", 1.0),
                "vol_z":      vol_data.get("z_score", 0.0),
            }

    return {"pump": False, "dump": False, "move_pct": 0.0}


def detect_overnight_gap(ohlcv_daily: list) -> dict[str, Any]:
    """
    Detect overnight gap between yesterday's close and today's open.
    Returns gap_pct (positive = gap up, negative = gap down).
    """
    if not ohlcv_daily or len(ohlcv_daily) < 2:
        return {"gap": False, "gap_pct": 0.0, "direction": "none"}

    prev_close = _safe(ohlcv_daily[-2][4])
    today_open = _safe(ohlcv_daily[-1][1])

    if prev_close <= 0 or today_open <= 0:
        return {"gap": False, "gap_pct": 0.0, "direction": "none"}

    gap_pct = (today_open - prev_close) / prev_close * 100.0

    return {
        "gap":        abs(gap_pct) >= 1.0,
        "gap_pct":    round(gap_pct, 2),
        "prev_close": round(prev_close, 6),
        "today_open": round(today_open, 6),
        "direction":  "up" if gap_pct > 0 else "down" if gap_pct < 0 else "none",
    }
