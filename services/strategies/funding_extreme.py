from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def signal_from_context(
    *,
    funding_rate_pct: float,
    long_crowded_threshold: float = 0.05,
    short_crowded_threshold: float = -0.01,
) -> dict[str, Any]:
    rate = _safe_float(funding_rate_pct, 0.0)

    ind = {
        "funding_rate_pct": round(rate, 4),
        "long_crowded_threshold": float(long_crowded_threshold),
        "short_crowded_threshold": float(short_crowded_threshold),
    }

    if rate >= float(long_crowded_threshold):
        return {"ok": True, "action": "sell", "reason": "funding_extreme_longs", "ind": ind}

    if rate <= float(short_crowded_threshold):
        return {"ok": True, "action": "buy", "reason": "funding_extreme_shorts", "ind": ind}

    return {"ok": True, "action": "hold", "reason": "funding_neutral", "ind": ind}
