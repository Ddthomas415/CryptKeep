from __future__ import annotations

from decimal import Decimal


def apply_market_slippage(*, price: Decimal, side: str, slippage_bps: Decimal) -> Decimal:
    px = Decimal(price)
    bps = Decimal(slippage_bps)
    if px <= 0 or bps <= 0:
        return px
    multiplier = Decimal("1")
    side_norm = str(side or "").lower()
    if side_norm == "buy":
        multiplier += (bps / Decimal("10000"))
    elif side_norm == "sell":
        multiplier -= (bps / Decimal("10000"))
    return px * multiplier


def compute_fee(*, notional: Decimal, fee_bps: Decimal) -> Decimal:
    n = Decimal(notional)
    bps = Decimal(fee_bps)
    if n <= 0 or bps <= 0:
        return Decimal("0")
    return n * (bps / Decimal("10000"))
