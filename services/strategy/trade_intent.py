from __future__ import annotations
"""
DEPRECATED — this module is in a transitional service family scheduled for
removal on 2026-07-01. See docs/ARCHITECTURE.md for the migration plan.
Import from the canonical path instead.
"""
import warnings as _warnings
_warnings.warn(
    f"{{__name__}} is deprecated and will be removed 2026-07-01. "
    "See docs/ARCHITECTURE.md for the canonical replacement.",
    DeprecationWarning,
    stacklevel=2,
)

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class TradeIntent:
    intent_id: str
    ts: str
    source: str  # manual|strategy|evidence
    strategy_id: str | None
    venue: str
    symbol: str
    side: str  # buy|sell
    order_type: str  # market|limit
    qty: float
    limit_price: float | None = None

    @staticmethod
    def manual(*, venue: str, symbol: str, side: str, order_type: str, qty: float, limit_price: float | None = None) -> "TradeIntent":
        return TradeIntent(
            intent_id=str(uuid.uuid4()),
            ts=now_iso(),
            source="manual",
            strategy_id=None,
            venue=str(venue).lower().strip(),
            symbol=str(symbol).strip(),
            side=str(side).lower().strip(),
            order_type=str(order_type).lower().strip(),
            qty=float(qty),
            limit_price=(float(limit_price) if limit_price is not None else None),
        )
