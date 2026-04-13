from __future__ import annotations

from typing import Any


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    w = values[-period:]
    return sum(w) / len(w) if w else None


def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss <= 1e-12:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_signal(cfg: dict, symbol: str, ohlcv: list) -> dict:
    strategy_cfg = dict(cfg.get("strategy") or {})

    fast_sma_period = int(_safe(strategy_cfg.get("fast_sma_period"), 20))
    trend_sma_period = int(_safe(strategy_cfg.get("trend_sma_period"), 50))
    rsi_period = int(_safe(strategy_cfg.get("rsi_period"), 14))

    min_pullback_pct = _safe(strategy_cfg.get("min_pullback_pct"), 2.0)
    max_pullback_pct = _safe(strategy_cfg.get("max_pullback_pct"), 12.0)

    rsi_reentry_max = _safe(strategy_cfg.get("rsi_reentry_max"), 55.0)
    rebound_confirm_pct = _safe(strategy_cfg.get("rebound_confirm_pct"), 0.0)
    trend_reclaim_tolerance_pct = _safe(strategy_cfg.get("trend_reclaim_tolerance_pct"), 1.5)

    exit_rsi = _safe(strategy_cfg.get("exit_rsi"), 68.0)
    stop_below_trend_sma = bool(strategy_cfg.get("stop_below_trend_sma", True))

    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 6]
    need = max(fast_sma_period, trend_sma_period, rsi_period) + 5
    if len(rows) < need:
        return {"action": "hold", "reason": "insufficient_data", "symbol": symbol, "indicators": {}}

    closes = [_safe(r[4]) for r in rows]
    current = closes[-1]
    prev = closes[-2]

    fast_sma = _sma(closes, fast_sma_period)
    trend_sma = _sma(closes, trend_sma_period)
    rsi = _rsi(closes, rsi_period)

    lookback = closes[-trend_sma_period:]
    recent_high = max(lookback) if lookback else current
    recent_low = min(lookback) if lookback else current

    pullback_pct = ((recent_high - current) / recent_high * 100.0) if recent_high > 0 else 0.0
    rebound_pct = ((current - prev) / prev * 100.0) if prev > 0 else 0.0

    trend_gap_pct = ((trend_sma - current) / trend_sma * 100.0) if trend_sma and trend_sma > 0 else 0.0
    trend_ok = bool(
        trend_sma is not None and (
            current >= trend_sma or trend_gap_pct <= trend_reclaim_tolerance_pct
        )
    )
    not_broken = bool(recent_low <= current <= recent_high)
    pullback_ok = min_pullback_pct <= pullback_pct <= max_pullback_pct
    rebound_ok = rebound_pct >= rebound_confirm_pct
    rsi_ok = (rsi is not None and rsi <= rsi_reentry_max)

    indicators = {
        "price": round(current, 8),
        "prev_close": round(prev, 8),
        "fast_sma": round(fast_sma, 8) if fast_sma is not None else None,
        "trend_sma": round(trend_sma, 8) if trend_sma is not None else None,
        "rsi": round(rsi, 4) if rsi is not None else None,
        "recent_high": round(recent_high, 8),
        "pullback_pct": round(pullback_pct, 4),
        "rebound_pct": round(rebound_pct, 4),
        "trend_ok": trend_ok,
        "trend_gap_pct": round(trend_gap_pct, 4),
        "pullback_ok": pullback_ok,
        "rebound_ok": rebound_ok,
    }

    if rsi is not None and rsi >= exit_rsi:
        return {"action": "sell", "reason": "rebound_mature_exit", "symbol": symbol, "indicators": indicators}

    if stop_below_trend_sma and trend_sma is not None and not trend_ok:
        return {"action": "hold", "reason": "breakdown_below_trend_sma", "symbol": symbol, "indicators": indicators}

    if trend_ok and not_broken and pullback_ok and rebound_ok and rsi_ok:
        return {"action": "buy", "reason": "pullback_recovery_entry", "symbol": symbol, "indicators": indicators}

    reasons = []
    if not trend_ok:
        reasons.append("not_in_uptrend")
    if not pullback_ok:
        reasons.append("pullback_out_of_range")
    if not rebound_ok:
        reasons.append("no_rebound_confirmation")
    if not rsi_ok:
        reasons.append(f"rsi>{rsi_reentry_max}")

    return {
        "action": "hold",
        "reason": ",".join(reasons) if reasons else "no_edge",
        "symbol": symbol,
        "indicators": indicators,
    }
