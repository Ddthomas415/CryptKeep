from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from core.models import Order, PortfolioState, Side


@dataclass(frozen=True)
class RiskConfig:
    max_trades_per_day: int = 10
    max_position_notional: float = 2000.0  # per symbol cap (qty * price)
    max_drawdown_frac: float = 0.10        # 10% from peak equity
    min_cash: float = 0.0                 # fail-closed if below


@dataclass
class RiskState:
    # Persisted by runner
    day_key: str = ""
    trades_today: int = 0
    peak_equity_today: float = 0.0


def calc_positions_notional(portfolio: PortfolioState, latest_prices: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for pos in portfolio.positions.values():
        lp = latest_prices.get(pos.symbol)
        if lp is None:
            continue
        out[pos.symbol] = out.get(pos.symbol, 0.0) + abs(float(pos.qty) * float(lp))
    return out


def allow_order(
    order: Order,
    portfolio: PortfolioState,
    latest_prices: Dict[str, float],
    cfg: RiskConfig,
    state: RiskState,
) -> Tuple[bool, str]:
    # Fail-closed on missing prices
    lp = latest_prices.get(order.symbol)
    if lp is None:
        return False, "NO_LATEST_PRICE"

    if portfolio.cash < cfg.min_cash:
        return False, "CASH_BELOW_MIN"

    # Trade count gate
    if state.trades_today >= cfg.max_trades_per_day:
        return False, "MAX_TRADES_PER_DAY"

    # Position notional gate (per symbol)
    notionals = calc_positions_notional(portfolio, latest_prices)
    cur_notional = notionals.get(order.symbol, 0.0)
    add_notional = abs(float(order.qty) * float(lp))
    if cur_notional + add_notional > cfg.max_position_notional:
        return False, "MAX_POSITION_NOTIONAL"

    # Drawdown gate (from peak equity tracked in state)
    peak = float(state.peak_equity_today or 0.0)
    if peak > 0.0:
        dd = (peak - float(portfolio.equity)) / peak
        if dd >= cfg.max_drawdown_frac:
            return False, "MAX_DRAWDOWN"

    return True, "OK"
