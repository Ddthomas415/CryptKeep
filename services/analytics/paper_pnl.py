from __future__ import annotations

from typing import Any, Dict

from services.analytics.portfolio_mtm import build_portfolio_mtm
from storage.paper_trading_sqlite import PaperTradingSQLite


def summarize_paper_pnl(
    *,
    prices: Dict[str, float] | None = None,
    store: PaperTradingSQLite | None = None,
) -> Dict[str, Any]:
    db = store or PaperTradingSQLite()
    cash_raw = db.get_state("cash_quote")
    realized_raw = db.get_state("realized_pnl")
    try:
        cash = float(cash_raw) if cash_raw is not None else 0.0
    except Exception:
        cash = 0.0
    try:
        realized = float(realized_raw) if realized_raw is not None else 0.0
    except Exception:
        realized = 0.0

    positions = db.list_positions(limit=5000)
    snap = build_portfolio_mtm(cash_quote=cash, positions=positions, prices=dict(prices or {}), realized_pnl=realized)
    return snap
