from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def signal_from_context(
    *,
    imbalance: float,
    buy_threshold: float = 0.15,
    sell_threshold: float = -0.15,
) -> dict[str, Any]:
    imb = _safe_float(imbalance, 0.0)

    ind = {
        "imbalance": round(imb, 4),
        "buy_threshold": float(buy_threshold),
        "sell_threshold": float(sell_threshold),
    }

    if imb >= float(buy_threshold):
        return {"ok": True, "action": "buy", "reason": "order_book_buy_pressure", "ind": ind}

    if imb <= float(sell_threshold):
        return {"ok": True, "action": "sell", "reason": "order_book_sell_pressure", "ind": ind}

    return {"ok": True, "action": "hold", "reason": "order_book_balanced", "ind": ind}
