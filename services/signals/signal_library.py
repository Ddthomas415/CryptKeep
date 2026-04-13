from __future__ import annotations

from typing import Any


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(v)))


def _sma(values: list[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
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


def momentum_score(ohlcv: list, *, short_bars: int = 12, long_bars: int = 48) -> float:
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 6]
    closes = [_safe(r[4]) for r in rows]
    if len(closes) < max(short_bars, long_bars) + 1:
        return 0.0

    cur = closes[-1]
    short_ref = closes[-1 - short_bars]
    long_ref = closes[-1 - long_bars]

    short_ret = ((cur - short_ref) / short_ref * 100.0) if short_ref > 0 else 0.0
    long_ret = ((cur - long_ref) / long_ref * 100.0) if long_ref > 0 else 0.0

    score = (short_ret * 3.0) + (long_ret * 2.0) + 50.0
    return round(_clamp(score), 4)


def relative_strength_score(
    symbol_return_pct: float,
    all_returns_pct: list[float],
) -> float:
    vals = [_safe(x) for x in all_returns_pct]
    if not vals:
        return 0.0
    target = _safe(symbol_return_pct)
    weaker = sum(1 for x in vals if x <= target)
    pct_rank = weaker / len(vals) * 100.0
    return round(_clamp(pct_rank), 4)


def volume_surge_score(ohlcv: list, *, baseline_bars: int = 20) -> float:
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 6]
    vols = [_safe(r[5]) for r in rows]
    if len(vols) < baseline_bars + 1:
        return 0.0

    cur = vols[-1]
    base = vols[-(baseline_bars + 1):-1]
    avg = sum(base) / len(base) if base else 0.0
    ratio = (cur / avg) if avg > 1e-12 else 0.0

    score = (ratio - 1.0) * 50.0
    return round(_clamp(score), 4)


def pullback_recovery_score(ohlcv: list, *, trend_bars: int = 50) -> float:
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 6]
    closes = [_safe(r[4]) for r in rows]
    if len(closes) < trend_bars + 2:
        return 0.0

    cur = closes[-1]
    prev = closes[-2]
    trend_sma = _sma(closes, trend_bars)
    rsi = _rsi(closes, 14)
    recent_high = max(closes[-trend_bars:]) if closes[-trend_bars:] else cur

    pullback_pct = ((recent_high - cur) / recent_high * 100.0) if recent_high > 0 else 0.0
    rebound_pct = ((cur - prev) / prev * 100.0) if prev > 0 else 0.0
    trend_gap_pct = ((trend_sma - cur) / trend_sma * 100.0) if trend_sma and trend_sma > 0 else 999.0

    score = 0.0
    if 2.0 <= pullback_pct <= 12.0:
        score += 35.0
    if rebound_pct >= 0.0:
        score += 20.0
    if trend_gap_pct <= 1.5:
        score += 25.0
    if rsi is not None and rsi <= 55.0:
        score += 20.0

    return round(_clamp(score), 4)


def illiquidity_risk_score(ohlcv: list, *, baseline_bars: int = 20) -> float:
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 6]
    if len(rows) < baseline_bars:
        return 100.0

    closes = [_safe(r[4]) for r in rows[-baseline_bars:]]
    vols = [_safe(r[5]) for r in rows[-baseline_bars:]]

    avg_close = sum(closes) / len(closes) if closes else 0.0
    avg_vol = sum(vols) / len(vols) if vols else 0.0
    notional = avg_close * avg_vol

    if notional <= 0:
        return 100.0

    if notional >= 1_000_000:
        return 0.0
    if notional >= 250_000:
        return 20.0
    if notional >= 100_000:
        return 40.0
    if notional >= 25_000:
        return 65.0
    return 85.0


def compute_signal_scores(
    *,
    ohlcv: list,
    symbol_return_pct: float,
    all_returns_pct: list[float],
) -> dict[str, float]:
    scores = {
        "momentum_score": momentum_score(ohlcv),
        "relative_strength_score": relative_strength_score(symbol_return_pct, all_returns_pct),
        "volume_surge_score": volume_surge_score(ohlcv),
        "pullback_recovery_score": pullback_recovery_score(ohlcv),
        "illiquidity_risk_score": illiquidity_risk_score(ohlcv),
    }
    return scores
