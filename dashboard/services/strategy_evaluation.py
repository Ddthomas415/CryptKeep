from __future__ import annotations

import math
from typing import Any

from services.backtest.leaderboard import run_strategy_leaderboard
from services.backtest.parity_engine import run_parity_backtest
from services.strategies.hypotheses import get_strategy_hypothesis


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(out):
        return float(default)
    return out


def _fmt_pct(value: Any) -> str:
    return f"{_fnum(value, 0.0):.2f}%"


def _fmt_num(value: Any) -> str:
    return f"{_fnum(value, 0.0):.2f}"


def _fmt_opt(value: Any) -> str:
    if value is None:
        return "-"
    try:
        out = float(value)
    except Exception:
        return "-"
    if not math.isfinite(out):
        return "-"
    return f"{out:.2f}"


def build_strategy_workbench(
    *,
    cfg: dict[str, Any],
    strategy_name: str,
    symbol: str,
    candles: list[list[Any]],
    warmup_bars: int = 50,
    initial_cash: float = 10_000.0,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    backtest = run_parity_backtest(
        cfg=dict(cfg or {}),
        symbol=str(symbol or ""),
        candles=list(candles or []),
        warmup_bars=int(warmup_bars),
        initial_cash=float(initial_cash),
        fee_bps=float(fee_bps),
        slippage_bps=float(slippage_bps),
    )
    leaderboard = run_strategy_leaderboard(
        base_cfg=dict(cfg or {}),
        symbol=str(symbol or ""),
        candles=list(candles or []),
        warmup_bars=int(warmup_bars),
        initial_cash=float(initial_cash),
        fee_bps=float(fee_bps),
        slippage_bps=float(slippage_bps),
    )
    return {
        "ok": bool(backtest.get("ok")) and bool(leaderboard.get("ok")),
        "strategy_name": str(strategy_name or ""),
        "backtest": backtest,
        "leaderboard": leaderboard,
        "hypothesis": get_strategy_hypothesis(strategy_name),
        "research_only": True,
        "execution_enabled": False,
    }


def build_scorecard_table_rows(scorecard: dict[str, Any] | None) -> list[dict[str, str]]:
    payload = dict(scorecard or {})
    return [
        {"metric": "Net Return After Costs", "value": _fmt_pct(payload.get("net_return_after_costs_pct")), "note": "Post-fee and slippage"},
        {"metric": "Max Drawdown", "value": _fmt_pct(payload.get("max_drawdown_pct")), "note": "Peak-to-trough loss"},
        {"metric": "Profit Factor", "value": _fmt_opt(payload.get("profit_factor")), "note": "Gross wins / gross losses"},
        {"metric": "Sharpe Ratio", "value": _fmt_opt(payload.get("sharpe_ratio")), "note": "Bar-based, not annualized"},
        {"metric": "Sortino Ratio", "value": _fmt_opt(payload.get("sortino_ratio")), "note": "Downside-only volatility"},
        {"metric": "Win Rate", "value": _fmt_pct(payload.get("win_rate_pct")), "note": "Closed-trade wins"},
        {"metric": "Expectancy", "value": _fmt_num(payload.get("expectancy")), "note": "Average realized PnL"},
        {
            "metric": "Exposure-Adjusted Return",
            "value": _fmt_pct(payload.get("exposure_adjusted_return_pct")),
            "note": "Return scaled by time in market",
        },
        {"metric": "Total Fees", "value": _fmt_num(payload.get("total_fees")), "note": "Applied fill-model costs"},
        {"metric": "Closed Trades", "value": str(int(_fnum(payload.get("closed_trades"), 0.0))), "note": "Realized PnL events"},
        {
            "metric": "Paper/Live Drift",
            "value": _fmt_opt(payload.get("paper_live_drift_pct")),
            "note": "Only populated when both modes exist",
        },
        {"metric": "Operational Incidents", "value": str(int(_fnum(payload.get("operational_incidents"), 0.0))), "note": "Recorded runtime issues"},
    ]


def build_regime_table_rows(regime_scorecards: dict[str, dict[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = ["bull", "bear", "chop", "high_vol", "low_vol"]
    payload = dict(regime_scorecards or {})
    for regime in order:
        score = dict(payload.get(regime) or {})
        if int(score.get("bars") or 0) <= 0:
            continue
        rows.append(
            {
                "regime": regime.replace("_", " ").title(),
                "bars": int(score.get("bars") or 0),
                "return_pct": round(_fnum(score.get("net_return_after_costs_pct"), 0.0), 2),
                "max_drawdown_pct": round(_fnum(score.get("max_drawdown_pct"), 0.0), 2),
                "win_rate_pct": round(_fnum(score.get("win_rate_pct"), 0.0), 2),
                "profit_factor": score.get("profit_factor"),
                "expectancy": round(_fnum(score.get("expectancy"), 0.0), 4),
                "closed_trades": int(score.get("closed_trades") or 0),
            }
        )
    return rows


def build_leaderboard_table_rows(result: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list((result or {}).get("rows") or []):
        rows.append(
            {
                "rank": int(item.get("rank") or 0),
                "candidate": str(item.get("candidate") or ""),
                "strategy": str(item.get("strategy") or ""),
                "leaderboard_score": round(_fnum(item.get("leaderboard_score"), 0.0), 4),
                "return_pct": round(_fnum(item.get("net_return_after_costs_pct"), 0.0), 2),
                "max_drawdown_pct": round(_fnum(item.get("max_drawdown_pct"), 0.0), 2),
                "regime_robustness": round(_fnum(item.get("regime_robustness"), 0.0), 3),
                "regime_dispersion_pct": round(_fnum(item.get("regime_return_dispersion_pct"), 0.0), 2),
                "slippage_sensitivity_pct": round(_fnum(item.get("slippage_sensitivity_pct"), 0.0), 2),
                "paper_live_drift_pct": item.get("paper_live_drift_pct"),
            }
        )
    return rows


def build_hypothesis_sections(hypothesis: dict[str, Any] | None) -> list[dict[str, Any]]:
    payload = dict(hypothesis or {})
    return [
        {"title": "Market Assumption", "items": [str(payload.get("market_assumption") or "No hypothesis loaded.")]},
        {"title": "Entry Rules", "items": [str(item) for item in list(payload.get("entry_rules") or [])]},
        {"title": "Exit Rules", "items": [str(item) for item in list(payload.get("exit_rules") or [])]},
        {"title": "No-Trade Rules", "items": [str(item) for item in list(payload.get("no_trade_rules") or [])]},
        {"title": "Invalidation Conditions", "items": [str(item) for item in list(payload.get("invalidation_conditions") or [])]},
        {"title": "Expected Failure Regimes", "items": [str(item).replace("_", " ").title() for item in list(payload.get("expected_failure_regimes") or [])]},
        {"title": "Notes", "items": [str(item) for item in list(payload.get("notes") or [])]},
    ]
