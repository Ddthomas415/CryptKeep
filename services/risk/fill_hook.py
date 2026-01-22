from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from services.risk.fill_ledger import FillLedgerDB

def _get(o: Any, k: str, default=None):
    if isinstance(o, dict):
        return o.get(k, default)
    return getattr(o, k, default)

def _sf(x, default=0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)

@dataclass(frozen=True)
class CanonFill:
    symbol: str
    realized_pnl_usd: float
    fee_usd: float
    meta: Dict[str, Any]

def normalize_fill(fill: Any) -> CanonFill:
    symbol = str(_get(fill, "symbol", "") or _get(fill, "market", "") or "")

    realized = None
    for k in ("realized_pnl_usd", "realized_pnl", "pnl_usd", "pnl"):
        v = _get(fill, k, None)
        if v is not None:
            realized = _sf(v, 0.0)
            break
    if realized is None:
        realized = 0.0

    fee = None
    for k in ("fee_usd", "fees_usd", "fee", "fees"):
        v = _get(fill, k, None)
        if v is not None:
            fee = _sf(v, 0.0)
            break
    if fee is None:
        fee = 0.0

    meta = {}
    try:
        if isinstance(fill, dict):
            meta["raw_keys"] = list(fill.keys())[:50]
    except Exception:
        pass

    return CanonFill(symbol=symbol, realized_pnl_usd=float(realized), fee_usd=float(fee), meta=meta)

def record_fill(exec_db: str, fill: Any) -> CanonFill:
    cf = normalize_fill(fill)
    FillLedgerDB(exec_db).insert_fill(
        symbol=cf.symbol,
        realized_pnl_usd=cf.realized_pnl_usd,
        fee_usd=cf.fee_usd,
        meta=cf.meta,
    )
    return cf
