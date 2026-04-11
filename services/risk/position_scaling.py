from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def build_scaling_limits(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(cfg or {})
    rcfg = dict(cfg.get("risk") or {})
    return {
        "enable_position_scaling": bool(rcfg.get("enable_position_scaling", True)),
        "max_adds_per_symbol": _safe_int(rcfg.get("max_adds_per_symbol", 2), 2),
        "min_profit_to_add_pct": _safe_float(rcfg.get("min_profit_to_add_pct", 1.5), 1.5),
        "scale_in_size_multiplier": _safe_float(rcfg.get("scale_in_size_multiplier", 0.5), 0.5),
    }


def summarize_position_for_scaling(position: dict[str, Any] | None, mid_price: float) -> dict[str, Any]:
    p = dict(position or {})
    qty = _safe_float(p.get("qty"), 0.0)
    avg_price = _safe_float(p.get("avg_price"), 0.0)

    pnl_pct = 0.0
    if qty > 0 and avg_price > 0 and mid_price > 0:
        pnl_pct = ((mid_price - avg_price) / avg_price) * 100.0

    return {
        "has_position": qty > 0,
        "qty": qty,
        "avg_price": avg_price,
        "pnl_pct": round(pnl_pct, 4),
    }


def evaluate_scale_in(
    *,
    position_summary: dict[str, Any],
    adds_used: int,
    limits: dict[str, Any],
) -> dict[str, Any]:
    if not bool(limits.get("enable_position_scaling", True)):
        return {"ok": False, "reason": "scale:disabled", "is_scale": False}

    has_position = bool(position_summary.get("has_position"))
    pnl_pct = _safe_float(position_summary.get("pnl_pct"), 0.0)
    max_adds = _safe_int(limits.get("max_adds_per_symbol", 2), 2)
    min_profit = _safe_float(limits.get("min_profit_to_add_pct", 1.5), 1.5)

    if not has_position:
        return {"ok": True, "reason": "scale:not_applicable_initial_entry", "is_scale": False}

    if adds_used >= max_adds:
        return {"ok": False, "reason": "scale:max_adds_reached", "is_scale": True}

    if pnl_pct < min_profit:
        return {"ok": False, "reason": "scale:min_profit_not_reached", "is_scale": True}

    return {
        "ok": True,
        "reason": "scale:pass",
        "is_scale": True,
        "size_multiplier": _safe_float(limits.get("scale_in_size_multiplier", 0.5), 0.5),
    }
