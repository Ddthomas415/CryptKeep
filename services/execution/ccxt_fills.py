from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from storage.pnl_store_sqlite import PnLStoreSQLite

def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)

def _fee_from_obj(obj: dict) -> tuple[float, Optional[str]]:
    if not isinstance(obj, dict):
        return 0.0, None
    fee = obj.get("fee")
    if isinstance(fee, dict):
        return _as_float(fee.get("cost")), (str(fee.get("currency")) if fee.get("currency") else None)
    fees = obj.get("fees")
    if isinstance(fees, list) and fees:
        total = 0.0
        ccy = None
        for f in fees:
            if isinstance(f, dict):
                total += _as_float(f.get("cost"))
                if not ccy and f.get("currency"):
                    ccy = str(f.get("currency"))
        return total, ccy
    return 0.0, None

def extract_fills_from_ccxt_order(
    order: dict,
    fallback_side: str,
    fallback_qty: float,
    fallback_price: float,
) -> List[dict]:
    fills: List[dict] = []
    if not isinstance(order, dict):
        return fills
    trades = order.get("trades")
    if isinstance(trades, list) and trades:
        for tr in trades:
            if not isinstance(tr, dict):
                continue
            q = _as_float(tr.get("amount") or tr.get("qty") or tr.get("filled"))
            px = _as_float(tr.get("price") or tr.get("avg") or tr.get("average"))
            side = str(tr.get("side") or fallback_side).lower()
            fee_cost, fee_ccy = _fee_from_obj(tr)
            if q > 0 and px > 0:
                fills.append({"side": side, "qty": q, "price": px, "fee": fee_cost, "fee_ccy": fee_ccy})
        return fills
    filled = _as_float(order.get("filled"))
    if filled > 0:
        px = _as_float(order.get("average") or order.get("avg") or order.get("price") or fallback_price)
        fee_cost, fee_ccy = _fee_from_obj(order)
        if px > 0:
            fills.append({"side": str(fallback_side).lower(), "qty": filled, "price": px, "fee": fee_cost, "fee_ccy": fee_ccy})
    return fills

async def record_fills_from_ccxt_order(
    pnl_store: PnLStoreSQLite,
    venue: str,
    symbol_norm: str,
    order: dict,
    fallback_side: str,
    fallback_qty: float,
    fallback_price: float,
) -> int:
    fills = extract_fills_from_ccxt_order(order, fallback_side, fallback_qty, fallback_price)
    n = 0
    for f in fills:
        try:
            await pnl_store.record_fill(
                venue=str(venue),
                symbol=str(symbol_norm),
                side=str(f.get("side") or fallback_side),
                qty=float(f.get("qty") or 0.0),
                price=float(f.get("price") or 0.0),
                fee=float(f.get("fee") or 0.0),
                fee_ccy=f.get("fee_ccy"),
            )
            n += 1
        except Exception as _err:
            pass  # suppressed: ccxt_fills.py
    return n
