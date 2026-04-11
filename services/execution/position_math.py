from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def apply_allocation_fill(
    *,
    action: str,
    fill_price: float,
    delta_alloc_pct: float,
    current_qty: float,
    current_avg_price: float,
    current_exposure_pct: float,
) -> dict[str, Any]:
    action = str(action or "").strip().lower()
    px = _safe_float(fill_price, 0.0)
    delta = abs(_safe_float(delta_alloc_pct, 0.0))
    qty = _safe_float(current_qty, 0.0)
    avg = _safe_float(current_avg_price, 0.0)
    exposure = max(0.0, _safe_float(current_exposure_pct, 0.0))

    if px <= 0 or delta <= 0 or action not in {"buy", "sell"}:
        return {
            "ok": False,
            "reason": "invalid_fill_inputs",
            "new_qty": qty,
            "new_avg_price": avg,
            "new_exposure_pct": exposure,
            "qty_delta": 0.0,
            "position_event": "none",
        }

    qty_delta = delta / px

    if action == "buy":
        new_qty = qty + qty_delta
        new_exposure = exposure + delta
        if qty <= 0 or avg <= 0:
            new_avg = px
            event = "open"
        else:
            new_avg = ((avg * qty) + (px * qty_delta)) / max(new_qty, 1e-12)
            event = "add"
    else:
        sell_qty = min(qty, qty_delta) if qty > 0 else 0.0
        new_qty = max(0.0, qty - sell_qty)
        new_exposure = max(0.0, exposure - delta)
        if new_qty <= 1e-12:
            new_avg = 0.0
            event = "close"
        else:
            new_avg = avg
            event = "reduce"

    return {
        "ok": True,
        "reason": "applied",
        "new_qty": round(new_qty, 8),
        "new_avg_price": round(new_avg, 8),
        "new_exposure_pct": round(new_exposure, 4),
        "qty_delta": round(qty_delta if action == "buy" else -qty_delta, 8),
        "position_event": event,
    }
