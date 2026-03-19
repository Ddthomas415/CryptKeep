from __future__ import annotations

import math
from statistics import pstdev
from typing import Any, Dict, Iterable, List

from services.backtest.parity_engine import run_parity_backtest
from services.strategies.presets import apply_preset


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(out):
        return float(default)
    return out


def _minmax_scale(values: Iterable[float], *, invert: bool = False) -> list[float]:
    rows = [float(v) for v in values]
    if not rows:
        return []
    lo = min(rows)
    hi = max(rows)
    if math.isclose(lo, hi):
        base = [0.5 for _ in rows]
    else:
        base = [(value - lo) / (hi - lo) for value in rows]
    if invert:
        return [1.0 - value for value in base]
    return base


def _bounded_ratio(value: Any, full_credit: float) -> float:
    if full_credit <= 0.0:
        return 0.0
    return float(max(0.0, min(_fnum(value, 0.0) / float(full_credit), 1.0)))


def _participation_quality(row: Dict[str, Any]) -> float:
    closed_trades = max(int(_fnum(row.get("closed_trades"), 0.0)), 0)
    exposure_fraction = max(_fnum(row.get("exposure_fraction"), 0.0), 0.0)
    trade_quality = _bounded_ratio(closed_trades, 3.0)
    exposure_quality = _bounded_ratio(exposure_fraction, 0.20)
    return float((0.8 * trade_quality) + (0.2 * exposure_quality))


def _thin_sample_penalty(row: Dict[str, Any]) -> float:
    closed_trades = max(int(_fnum(row.get("closed_trades"), 0.0)), 0)
    exposure_fraction = max(_fnum(row.get("exposure_fraction"), 0.0), 0.0)
    if closed_trades <= 0:
        return 0.35
    if closed_trades == 1:
        return 0.05
    if closed_trades == 2 and exposure_fraction < 0.05:
        return 0.02
    return 0.0


def default_strategy_candidates(base_cfg: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    cfg = dict(base_cfg or {})
    return [
        {"candidate": "ema_cross_default", "cfg": apply_preset(cfg, "ema_cross_default")},
        {"candidate": "mean_reversion_default", "cfg": apply_preset(cfg, "mean_reversion_default")},
        {"candidate": "breakout_default", "cfg": apply_preset(cfg, "breakout_default")},
    ]


def _regime_summary(regime_scorecards: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    represented = {
        regime: score
        for regime, score in dict(regime_scorecards or {}).items()
        if int(score.get("bars") or 0) > 0
    }
    returns = [_fnum(score.get("net_return_after_costs_pct"), 0.0) for score in represented.values()]
    positive = sum(1 for value in returns if value >= 0.0)
    robustness = (positive / len(returns)) if returns else 0.0
    dispersion = float(pstdev(returns)) if len(returns) >= 2 else 0.0
    return {
        "represented_regimes": sorted(represented.keys()),
        "represented_regime_count": int(len(represented)),
        "regime_robustness": float(robustness),
        "regime_return_dispersion_pct": float(dispersion),
    }


def rank_strategy_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = [dict(row) for row in list(rows or [])]
    if not ranked:
        return []

    returns = _minmax_scale([_fnum(row.get("net_return_after_costs_pct"), 0.0) for row in ranked])
    drawdowns = _minmax_scale([_fnum(row.get("max_drawdown_pct"), 0.0) for row in ranked], invert=True)
    robustness = _minmax_scale([_fnum(row.get("regime_robustness"), 0.0) for row in ranked])
    dispersions = _minmax_scale([_fnum(row.get("regime_return_dispersion_pct"), 0.0) for row in ranked], invert=True)
    slippage = _minmax_scale([_fnum(row.get("slippage_sensitivity_pct"), 0.0) for row in ranked], invert=True)
    drifts = _minmax_scale(
        [abs(_fnum(row.get("paper_live_drift_pct"), 0.0)) if row.get("paper_live_drift_pct") is not None else 0.0 for row in ranked],
        invert=True,
    )
    participation = _minmax_scale([_participation_quality(row) for row in ranked])

    for idx, row in enumerate(ranked):
        stability_component = (0.7 * robustness[idx]) + (0.3 * dispersions[idx])
        thin_sample_penalty = _thin_sample_penalty(row)
        score = (
            0.30 * returns[idx]
            + 0.18 * drawdowns[idx]
            + 0.18 * stability_component
            + 0.14 * slippage[idx]
            + 0.10 * drifts[idx]
            + 0.10 * participation[idx]
            - thin_sample_penalty
        )
        row["leaderboard_score"] = float(round(score, 6))
        row["leaderboard_components"] = {
            "return_component": float(round(returns[idx], 6)),
            "drawdown_component": float(round(drawdowns[idx], 6)),
            "stability_component": float(round(stability_component, 6)),
            "slippage_component": float(round(slippage[idx], 6)),
            "drift_component": float(round(drifts[idx], 6)),
            "participation_component": float(round(participation[idx], 6)),
            "thin_sample_penalty": float(round(thin_sample_penalty, 6)),
        }

    ranked.sort(
        key=lambda row: (
            -_fnum(row.get("leaderboard_score"), 0.0),
            -_fnum(row.get("net_return_after_costs_pct"), 0.0),
            _fnum(row.get("max_drawdown_pct"), 0.0),
        )
    )
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = int(idx)
    return ranked


def run_strategy_leaderboard(
    *,
    base_cfg: Dict[str, Any],
    symbol: str,
    candles: List[list[Any]],
    warmup_bars: int = 50,
    initial_cash: float = 10_000.0,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    stressed_slippage_bps: float | None = None,
    candidates: List[Dict[str, Any]] | None = None,
    paper_live_drifts: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    active_candidates = list(candidates or default_strategy_candidates(base_cfg))
    stress_slippage = float(
        stressed_slippage_bps
        if stressed_slippage_bps is not None
        else (max(float(slippage_bps) + 10.0, float(slippage_bps) * 2.0 if float(slippage_bps) > 0.0 else 10.0))
    )
    rows: List[Dict[str, Any]] = []

    for item in active_candidates:
        candidate_name = str(item.get("candidate") or "candidate")
        cfg = dict(item.get("cfg") or {})
        base_result = run_parity_backtest(
            cfg=cfg,
            symbol=str(symbol or ""),
            candles=list(candles or []),
            warmup_bars=int(warmup_bars),
            initial_cash=float(initial_cash),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        stress_result = run_parity_backtest(
            cfg=cfg,
            symbol=str(symbol or ""),
            candles=list(candles or []),
            warmup_bars=int(warmup_bars),
            initial_cash=float(initial_cash),
            fee_bps=float(fee_bps),
            slippage_bps=float(stress_slippage),
        )
        scorecard = dict(base_result.get("scorecard") or {})
        regime_summary = _regime_summary(dict(base_result.get("regime_scorecards") or {}))
        strategy_name = str(scorecard.get("strategy") or cfg.get("strategy", {}).get("name") or "")
        paper_live_drift_pct = None
        if isinstance(paper_live_drifts, dict):
            paper_live_drift_pct = paper_live_drifts.get(candidate_name)
            if paper_live_drift_pct is None:
                paper_live_drift_pct = paper_live_drifts.get(strategy_name)

        row = {
            "candidate": candidate_name,
            "strategy": strategy_name,
            "symbol": str(symbol or ""),
            "net_return_after_costs_pct": _fnum(scorecard.get("net_return_after_costs_pct"), 0.0),
            "max_drawdown_pct": _fnum(scorecard.get("max_drawdown_pct"), 0.0),
            "profit_factor": scorecard.get("profit_factor"),
            "sharpe_ratio": scorecard.get("sharpe_ratio"),
            "sortino_ratio": scorecard.get("sortino_ratio"),
            "expectancy": _fnum(scorecard.get("expectancy"), 0.0),
            "win_rate_pct": _fnum(scorecard.get("win_rate_pct"), 0.0),
            "closed_trades": int(_fnum(scorecard.get("closed_trades"), 0.0)),
            "trade_count": int(_fnum(base_result.get("trade_count"), 0.0)),
            "exposure_fraction": _fnum(scorecard.get("exposure_fraction"), 0.0),
            "exposure_adjusted_return_pct": _fnum(scorecard.get("exposure_adjusted_return_pct"), 0.0),
            "paper_live_drift_pct": float(paper_live_drift_pct) if paper_live_drift_pct is not None else None,
            "slippage_sensitivity_pct": float(
                _fnum(scorecard.get("net_return_after_costs_pct"), 0.0)
                - _fnum((stress_result.get("scorecard") or {}).get("net_return_after_costs_pct"), 0.0)
            ),
            "scorecard": scorecard,
            "regime_scorecards": dict(base_result.get("regime_scorecards") or {}),
            "stress_scorecard": dict(stress_result.get("scorecard") or {}),
        }
        row.update(regime_summary)
        rows.append(row)

    ranked_rows = rank_strategy_rows(rows)
    return {
        "ok": True,
        "symbol": str(symbol or ""),
        "candidate_count": int(len(ranked_rows)),
        "base_slippage_bps": float(slippage_bps),
        "stressed_slippage_bps": float(stress_slippage),
        "rows": ranked_rows,
    }
