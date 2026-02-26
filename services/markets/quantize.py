from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING, getcontext
from typing import Optional

getcontext().prec = 28

def _D(x: float) -> Decimal:
    return Decimal(str(x))

def _quantize_step(x: float, step: float, *, mode: str) -> float:
    if step is None or step <= 0:
        return float(x)
    dx = _D(float(x))
    ds = _D(float(step))
    q = dx / ds
    if mode == "floor":
        n = q.to_integral_value(rounding=ROUND_FLOOR)
    elif mode == "ceil":
        n = q.to_integral_value(rounding=ROUND_CEILING)
    else:
        raise ValueError("mode must be floor|ceil")
    return float(n * ds)

def quantize_amount(amount: float, qty_step: Optional[float]) -> float:
    # Always round DOWN size (safer)
    if not qty_step:
        return float(amount)
    return _quantize_step(float(amount), float(qty_step), mode="floor")

def quantize_price(price: float, price_tick: Optional[float], side: str) -> float:
    # Don't worsen price:
    # buy -> round DOWN (never pay more)
    # sell -> round UP (never sell for less)
    if not price_tick:
        return float(price)
    s = (side or "").strip().lower()
    mode = "floor" if s == "buy" else "ceil"
    return _quantize_step(float(price), float(price_tick), mode=mode)
