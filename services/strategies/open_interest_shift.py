from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def signal_from_context(
    *,
    open_interest_now: float,
    open_interest_prev: float,
    price_change_pct: float,
    oi_rise_threshold_pct: float = 5.0,
    oi_drop_threshold_pct: float = -5.0,
) -> dict[str, Any]:
    now = _safe_float(open_interest_now, 0.0)
    prev = _safe_float(open_interest_prev, 0.0)
    px = _safe_float(price_change_pct, 0.0)

    oi_change_pct = ((now - prev) / prev * 100.0) if prev > 0 else 0.0

    ind = {
        "open_interest_now": round(now, 4),
        "open_interest_prev": round(prev, 4),
        "oi_change_pct": round(oi_change_pct, 4),
        "price_change_pct": round(px, 4),
    }

    if oi_change_pct >= float(oi_rise_threshold_pct) and px > 0:
        return {"ok": True, "action": "buy", "reason": "oi_rising_with_price", "ind": ind}

    if oi_change_pct >= float(oi_rise_threshold_pct) and px < 0:
        return {"ok": True, "action": "sell", "reason": "oi_rising_against_price", "ind": ind}

    if oi_change_pct <= float(oi_drop_threshold_pct):
        return {"ok": True, "action": "hold", "reason": "oi_unwinding", "ind": ind}

    return {"ok": True, "action": "hold", "reason": "oi_neutral", "ind": ind}
