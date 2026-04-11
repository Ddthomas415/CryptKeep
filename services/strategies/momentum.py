from __future__ import annotations

import math
from typing import Any


def _safe(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except Exception:
        return default


def _sma(closes: list[float], period: int) -> float | None:
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_signal(
    *,
    cfg: dict[str, Any],
    symbol: str,
    ohlcv: list[list[Any]],
) -> dict[str, Any]:
    """
    Momentum strategy:
    - Buy strong movers above trend, but not extremely overbought
    - Sell on loss of trend or overbought exhaustion

    Expected cfg shape:
      cfg = {
        "strategy": {
          "min_change_pct": 5.0,
          "max_rsi_entry": 75.0,
          "rsi_exit": 80.0,
          "sma_period": 20,
          "rsi_period": 14,
          "stop_below_sma": True,
        }
      }
    """
    strategy_cfg = dict(cfg.get("strategy") or {})
    min_change_pct = _safe(strategy_cfg.get("min_change_pct"), 5.0)
    max_rsi_entry = _safe(strategy_cfg.get("max_rsi_entry"), 75.0)
    rsi_exit = _safe(strategy_cfg.get("rsi_exit"), 80.0)
    sma_period = int(_safe(strategy_cfg.get("sma_period"), 20))
    rsi_period = int(_safe(strategy_cfg.get("rsi_period"), 14))
    stop_below_sma = bool(strategy_cfg.get("stop_below_sma", True))

    rows = [row for row in list(ohlcv or []) if isinstance(row, (list, tuple)) and len(row) >= 6]
    if len(rows) < max(sma_period, rsi_period) + 2:
        return {
            "action": "hold",
            "reason": "insufficient_data",
            "symbol": symbol,
            "indicators": {},
        }

    closes = [_safe(r[4]) for r in rows if _safe(r[4]) > 0]
    if len(closes) < max(sma_period, rsi_period) + 1:
        return {
            "action": "hold",
            "reason": "insufficient_closes",
            "symbol": symbol,
            "indicators": {},
        }

    current = closes[-1]
    prev = closes[-2]
    sma = _sma(closes, sma_period)
    rsi = _rsi(closes, rsi_period)

    # Simple lookback momentum proxy from recent closes
    change_pct = 0.0
    if prev > 0:
        change_pct = ((current - prev) / prev) * 100.0

    above_sma = bool(sma is not None and current > sma)
    below_sma = bool(sma is not None and current < sma)

    indicators = {
        "price": round(current, 8),
        "prev_close": round(prev, 8),
        "change_pct": round(change_pct, 4),
        "sma": round(sma, 8) if sma is not None else None,
        "rsi": round(rsi, 4) if rsi is not None else None,
        "above_sma": above_sma,
        "below_sma": below_sma,
    }

    # Exit conditions
    if rsi is not None and rsi >= rsi_exit:
        return {
            "action": "sell",
            "reason": "rsi_overbought_exit",
            "symbol": symbol,
            "indicators": indicators,
        }

    if stop_below_sma and below_sma:
        return {
            "action": "sell",
            "reason": "lost_trend_below_sma",
            "symbol": symbol,
            "indicators": indicators,
        }

    # Entry conditions
    momentum_ok = change_pct >= min_change_pct
    trend_ok = above_sma
    rsi_ok = (rsi is None) or (rsi < max_rsi_entry)

    if momentum_ok and trend_ok and rsi_ok:
        return {
            "action": "buy",
            "reason": "momentum_entry",
            "symbol": symbol,
            "indicators": indicators,
        }

    reasons: list[str] = []
    if not momentum_ok:
        reasons.append(f"change_pct<{min_change_pct}")
    if not trend_ok:
        reasons.append("not_above_sma")
    if not rsi_ok:
        reasons.append(f"rsi>={max_rsi_entry}")

    return {
        "action": "hold",
        "reason": ",".join(reasons) if reasons else "no_signal",
        "symbol": symbol,
        "indicators": indicators,
    }
