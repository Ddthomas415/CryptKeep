from __future__ import annotations
from dataclasses import dataclass

@dataclass
class FillResult:
    exec_px: float
    fee: float
    notional: float

def apply_fee_slippage(
    *,
    mid_px: float,
    side: str,
    qty: float,
    fee_bps: float,
    slippage_bps: float,
) -> FillResult:
    """
    Deterministic fill model for PAPER + BACKTEST parity.
    - BUY executes at mid + slippage
    - SELL executes at mid - slippage
    - fee is charged on notional: fee_bps / 10_000
    NOTE: If you want perfect parity, PAPER engine should call this same function.
    """
    px = float(mid_px)
    q = float(qty)
    fb = float(fee_bps) / 10000.0
    sb = float(slippage_bps) / 10000.0
    if q <= 0 or px <= 0:
        return FillResult(exec_px=0.0, fee=0.0, notional=0.0)
    s = str(side).lower().strip()
    slip = px * sb
    exec_px = px + slip if s == "buy" else max(0.0, px - slip)
    notional = q * exec_px
    fee = notional * fb
    return FillResult(exec_px=exec_px, fee=fee, notional=notional)
