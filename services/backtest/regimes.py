from __future__ import annotations

import math
from typing import Any, Dict, List

from services.backtest.scorecard import build_strategy_scorecard


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(out):
        return float(default)
    return out


def _mean(values: List[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _sample_stddev(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    variance = sum((value - mu) ** 2 for value in values) / float(len(values) - 1)
    return math.sqrt(max(variance, 0.0))


def classify_market_regimes(
    candles: List[list[Any]],
    *,
    trend_window: int = 20,
    vol_window: int = 20,
    bull_threshold_pct: float = 0.03,
    bear_threshold_pct: float = -0.03,
    low_vol_threshold: float = 0.004,
    high_vol_threshold: float = 0.02,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    closes = [_fnum(row[4], 0.0) for row in list(candles or []) if isinstance(row, (list, tuple)) and len(row) >= 5]
    ts_values = [row[0] for row in list(candles or []) if isinstance(row, (list, tuple)) and len(row) >= 5]

    returns: List[float] = [0.0]
    for idx in range(1, len(closes)):
        prev = closes[idx - 1]
        cur = closes[idx]
        returns.append(((cur / prev) - 1.0) if prev > 0.0 else 0.0)

    for idx, close_px in enumerate(closes):
        trend_start = max(0, idx - max(1, int(trend_window)) + 1)
        vol_start = max(0, idx - max(1, int(vol_window)) + 1)
        base = closes[trend_start]
        trend_return = ((close_px / base) - 1.0) if base > 0.0 else 0.0
        realized_vol = _sample_stddev(returns[vol_start : idx + 1])

        if realized_vol >= float(high_vol_threshold):
            regime = "high_vol"
        elif trend_return >= float(bull_threshold_pct):
            regime = "bull"
        elif trend_return <= float(bear_threshold_pct):
            regime = "bear"
        elif realized_vol <= float(low_vol_threshold):
            regime = "low_vol"
        else:
            regime = "chop"

        rows.append(
            {
                "ts_ms": ts_values[idx],
                "close": float(close_px),
                "trend_return_pct": float(trend_return * 100.0),
                "realized_vol": float(realized_vol),
                "regime": regime,
            }
        )
    return rows


def build_regime_scorecards(
    *,
    strategy: str,
    symbol: str,
    trades: List[Dict[str, Any]],
    equity: List[Dict[str, Any]],
    regime_rows: List[Dict[str, Any]],
    fee_bps: float,
    slippage_bps: float,
) -> Dict[str, Dict[str, Any]]:
    regime_by_ts = {row.get("ts_ms"): str(row.get("regime") or "unknown") for row in list(regime_rows or [])}
    regime_names = ["bull", "bear", "chop", "high_vol", "low_vol"]
    out: Dict[str, Dict[str, Any]] = {}

    for regime in regime_names:
        equity_rows = [row for row in list(equity or []) if regime_by_ts.get(row.get("ts_ms")) == regime]
        trade_rows = [row for row in list(trades or []) if regime_by_ts.get(row.get("ts_ms")) == regime]
        initial_equity = _fnum((equity_rows[0] if equity_rows else {}).get("equity"), 0.0)
        scorecard = build_strategy_scorecard(
            strategy=strategy,
            symbol=symbol,
            trades=trade_rows,
            equity=equity_rows,
            initial_cash=initial_equity,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            operational_incidents=0,
        )
        scorecard["bars"] = int(len(equity_rows))
        scorecard["regime"] = regime
        scorecard["start_ts_ms"] = (equity_rows[0] if equity_rows else {}).get("ts_ms")
        scorecard["end_ts_ms"] = (equity_rows[-1] if equity_rows else {}).get("ts_ms")
        out[regime] = scorecard

    return out
