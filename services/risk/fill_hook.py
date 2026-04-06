from __future__ import annotations

# CBP_FILL_HOOK_UPDATES_RISK_DAILY_V1
import logging

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional

from services.risk.fill_ledger import FillLedgerDB
from services.risk.risk_daily import RiskDailyDB

_LOG = logging.getLogger(__name__)

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
        _LOG.exception(
            "fill_hook normalize_fill metadata capture failed venue=%s fill_id=%s",
            _get(fill, "venue", ""),
            _get(fill, "fill_id", ""),
        )

    return CanonFill(symbol=symbol, realized_pnl_usd=float(realized), fee_usd=float(fee), meta=meta)

def record_fill(exec_db: str, fill: Any) -> CanonFill:
    cf = normalize_fill(fill)

    # Extract idempotency key for daily rollup
    venue = "unknown"
    fill_id = ""
    try:
        if isinstance(fill, dict):
            get = fill.get
            venue = str(get("venue") or get("exchange") or "unknown")
            fill_id = str(get("fill_id") or get("id") or "")
        else:
            venue = str(getattr(fill, "venue", None) or getattr(fill, "exchange", None) or "unknown")
            fill_id = str(getattr(fill, "fill_id", None) or getattr(fill, "id", None) or "")
    except Exception:
        pass

    # If missing fill_id, synthesize a deterministic one from stable fields
    if not fill_id:
        try:
            raw = f"{venue}|{cf.symbol}|{cf.realized_pnl_usd}|{cf.fee_usd}"
            fill_id = "synthetic:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        except Exception:
            fill_id = "synthetic:unknown"
    FillLedgerDB(exec_db).insert_fill(
        symbol=cf.symbol,
        realized_pnl_usd=cf.realized_pnl_usd,
        fee_usd=cf.fee_usd,
        meta=cf.meta,
    )
    # Update deterministic daily rollup (idempotent per venue+fill_id)
    try:
        RiskDailyDB(exec_db).apply_fill_once(
            venue=str(venue),
            fill_id=str(fill_id),
            realized_pnl_usd=float(cf.realized_pnl_usd),
            fee_usd=float(cf.fee_usd),
        )
    except Exception:
        pass

    return cf
