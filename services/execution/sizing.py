from __future__ import annotations

import math
from typing import Any, Dict, Tuple


def estimate_notional(*, qty: float, price: float) -> float:
    return float(qty) * float(price)


def quote_to_base_qty(
    *,
    quote_notional: float,
    price: float,
    min_qty: float = 0.0,
    qty_step: float = 0.0,
) -> float:
    p = float(price)
    if p <= 0:
        return 0.0
    qty = float(quote_notional) / p
    if qty_step and qty_step > 0:
        steps = math.floor(qty / float(qty_step))
        qty = steps * float(qty_step)
    if min_qty and qty < float(min_qty):
        return 0.0
    return float(max(0.0, qty))


def validate_order_size(
    *,
    qty: float,
    price: float,
    min_notional: float = 0.0,
    min_qty: float = 0.0,
) -> Tuple[bool, str, Dict[str, Any]]:
    q = float(qty)
    p = float(price)
    if q <= 0:
        return False, "qty_nonpositive", {"qty": q}
    if p <= 0:
        return False, "price_nonpositive", {"price": p}
    n = estimate_notional(qty=q, price=p)
    if min_qty and q < float(min_qty):
        return False, "min_qty", {"qty": q, "min_qty": float(min_qty), "notional": n}
    if min_notional and n < float(min_notional):
        return False, "min_notional", {"notional": n, "min_notional": float(min_notional)}
    return True, "ok", {"qty": q, "price": p, "notional": n}
