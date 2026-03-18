from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(out):
        return float(default)
    return out


def _mean(values: Iterable[float]) -> float:
    rows = [float(v) for v in values]
    return float(sum(rows) / len(rows)) if rows else 0.0


def _sample_stddev(values: Iterable[float]) -> float:
    rows = [float(v) for v in values]
    if len(rows) < 2:
        return 0.0
    mu = _mean(rows)
    variance = sum((v - mu) ** 2 for v in rows) / float(len(rows) - 1)
    return math.sqrt(max(variance, 0.0))


def _equity_returns(equity: List[Dict[str, Any]]) -> List[float]:
    out: List[float] = []
    prev_equity: float | None = None
    for row in list(equity or []):
        cur = _fnum(row.get("equity"), 0.0)
        if prev_equity is None:
            prev_equity = cur
            continue
        if prev_equity > 0:
            out.append((cur / prev_equity) - 1.0)
        prev_equity = cur
    return out


def _max_drawdown_pct(equity: List[Dict[str, Any]]) -> float:
    peak: float | None = None
    max_dd = 0.0
    for row in list(equity or []):
        cur = _fnum(row.get("equity"), 0.0)
        if peak is None or cur > peak:
            peak = cur
            continue
        if peak <= 0:
            continue
        dd = (peak - cur) / peak
        if dd > max_dd:
            max_dd = dd
    return float(max_dd * 100.0)


def _exposure_fraction(equity: List[Dict[str, Any]]) -> float:
    rows = list(equity or [])
    if not rows:
        return 0.0
    exposed = sum(1 for row in rows if _fnum(row.get("pos_qty"), 0.0) > 1e-12)
    return float(exposed / len(rows))


def build_strategy_scorecard(
    *,
    strategy: str,
    symbol: str,
    trades: List[Dict[str, Any]],
    equity: List[Dict[str, Any]],
    initial_cash: float,
    fee_bps: float,
    slippage_bps: float,
    paper_return_pct: float | None = None,
    live_return_pct: float | None = None,
    operational_incidents: int = 0,
) -> Dict[str, Any]:
    final_equity = _fnum((equity[-1] if equity else {}).get("equity"), _fnum(initial_cash, 0.0))
    initial_cash_f = _fnum(initial_cash, 0.0)
    net_return_after_costs_pct = (
        (((final_equity / initial_cash_f) - 1.0) * 100.0) if initial_cash_f > 0.0 else 0.0
    )
    max_drawdown_pct = _max_drawdown_pct(equity)

    closed_pnls = [
        _fnum(trade.get("realized_pnl"), 0.0)
        for trade in list(trades or [])
        if trade.get("realized_pnl") is not None
    ]
    wins = [pnl for pnl in closed_pnls if pnl > 0.0]
    losses = [pnl for pnl in closed_pnls if pnl < 0.0]
    gross_profit = float(sum(wins))
    gross_loss_abs = float(abs(sum(losses)))
    profit_factor = (gross_profit / gross_loss_abs) if gross_loss_abs > 0.0 else None
    avg_win = _mean(wins)
    avg_loss = _mean(losses)
    expectancy = _mean(closed_pnls)
    win_rate_pct = (100.0 * len(wins) / len(closed_pnls)) if closed_pnls else 0.0

    step_returns = _equity_returns(equity)
    ret_mean = _mean(step_returns)
    ret_std = _sample_stddev(step_returns)
    downside_returns = [ret for ret in step_returns if ret < 0.0]
    downside_std = _sample_stddev(downside_returns)
    # Bar-based ratios only. No annualization is implied because bar spacing varies by caller.
    sharpe_ratio = (ret_mean / ret_std) if ret_std > 0.0 else None
    sortino_ratio = (ret_mean / downside_std) if downside_std > 0.0 else None

    exposure_fraction = _exposure_fraction(equity)
    exposure_adjusted_return_pct = (
        net_return_after_costs_pct / exposure_fraction if exposure_fraction > 0.0 else 0.0
    )

    paper_live_drift_pct = None
    if paper_return_pct is not None and live_return_pct is not None:
        paper_live_drift_pct = float(_fnum(live_return_pct) - _fnum(paper_return_pct))

    return {
        "strategy": str(strategy or ""),
        "symbol": str(symbol or ""),
        "closed_trades": int(len(closed_pnls)),
        "net_return_after_costs_pct": float(net_return_after_costs_pct),
        "max_drawdown_pct": float(max_drawdown_pct),
        "profit_factor": float(profit_factor) if profit_factor is not None else None,
        "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio is not None else None,
        "sortino_ratio": float(sortino_ratio) if sortino_ratio is not None else None,
        "win_rate_pct": float(win_rate_pct),
        "avg_win": float(avg_win),
        "avg_loss": float(avg_loss),
        "expectancy": float(expectancy),
        "exposure_fraction": float(exposure_fraction),
        "exposure_adjusted_return_pct": float(exposure_adjusted_return_pct),
        "paper_live_drift_pct": float(paper_live_drift_pct) if paper_live_drift_pct is not None else None,
        "operational_incidents": int(operational_incidents),
        "total_fees": float(sum(_fnum(trade.get("fee"), 0.0) for trade in list(trades or []))),
        "fee_bps": float(_fnum(fee_bps, 0.0)),
        "slippage_bps": float(_fnum(slippage_bps, 0.0)),
    }


def scorecard_row(scorecard: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "strategy": str(scorecard.get("strategy") or ""),
        "symbol": str(scorecard.get("symbol") or ""),
        "net_return_after_costs_pct": _fnum(scorecard.get("net_return_after_costs_pct"), 0.0),
        "max_drawdown_pct": _fnum(scorecard.get("max_drawdown_pct"), 0.0),
        "profit_factor": scorecard.get("profit_factor"),
        "sharpe_ratio": scorecard.get("sharpe_ratio"),
        "sortino_ratio": scorecard.get("sortino_ratio"),
        "win_rate_pct": _fnum(scorecard.get("win_rate_pct"), 0.0),
        "expectancy": _fnum(scorecard.get("expectancy"), 0.0),
        "exposure_adjusted_return_pct": _fnum(scorecard.get("exposure_adjusted_return_pct"), 0.0),
        "paper_live_drift_pct": scorecard.get("paper_live_drift_pct"),
        "operational_incidents": int(_fnum(scorecard.get("operational_incidents"), 0.0)),
        "closed_trades": int(_fnum(scorecard.get("closed_trades"), 0.0)),
    }
