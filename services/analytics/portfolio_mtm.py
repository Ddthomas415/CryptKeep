from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from services.analytics.mtm_equity import compute_mtm_equity


def build_portfolio_mtm(
    *,
    cash_quote: float,
    positions: Iterable[Dict[str, Any]],
    prices: Dict[str, float],
    realized_pnl: float = 0.0,
) -> Dict[str, Any]:
    snap = compute_mtm_equity(
        cash_quote=float(cash_quote),
        positions=list(positions or []),
        prices=dict(prices or {}),
        realized_pnl=float(realized_pnl),
    )
    snap["ts"] = datetime.now(timezone.utc).isoformat()
    return snap
