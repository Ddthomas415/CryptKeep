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
        # Core signals (v1)
        "momentum_score": momentum_score(ohlcv),
        "relative_strength_score": relative_strength_score(symbol_return_pct, all_returns_pct),
        "volume_surge_score": volume_surge_score(ohlcv),
        "pullback_recovery_score": pullback_recovery_score(ohlcv),
        "illiquidity_risk_score": illiquidity_risk_score(ohlcv),
        # Extended signals (v2)
        "volatility_regime_score": volatility_regime_score(ohlcv),
        "consolidation_score": consolidation_score(ohlcv),
        "spread_quality_score": spread_quality_score(ohlcv),
        "trend_quality_score": trend_quality_score(ohlcv),
        "illiquidity_risk_score_v2": illiquidity_risk_score_v2(ohlcv),
    }
    return scores


# ---------------------------------------------------------------------------
# New signals added 2026-04
# ---------------------------------------------------------------------------

def volatility_regime_score(ohlcv: list, *, atr_bars: int = 14, regime_bars: int = 50) -> float:
    """Score 0-100 indicating how favourable the current volatility regime is.

    High score = moderate volatility (good for entries).
    Low score  = either too quiet (fee bleed) or too explosive (whipsaw risk).
    Returns 50 when insufficient data.
    """
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 5]
    if len(rows) < max(atr_bars, regime_bars) + 1:
        return 50.0

    # ATR over atr_bars
    atrs = []
    for i in range(1, len(rows)):
        h = _safe(rows[i][2])
        l = _safe(rows[i][3])
        prev_c = _safe(rows[i - 1][4])
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        atrs.append(tr)

    if len(atrs) < atr_bars:
        return 50.0

    recent_atr = sum(atrs[-atr_bars:]) / atr_bars
    baseline_atr = sum(atrs[-regime_bars:]) / len(atrs[-regime_bars:]) if len(atrs) >= regime_bars else recent_atr
    cur_close = _safe(rows[-1][4])

    if cur_close <= 0 or baseline_atr <= 0:
        return 50.0

    atr_pct = recent_atr / cur_close * 100.0
    atr_ratio = recent_atr / baseline_atr

    # Sweet spot: ATR 0.5–3% of price and not spiking vs baseline
    if 0.5 <= atr_pct <= 3.0 and 0.5 <= atr_ratio <= 2.0:
        score = 80.0 - abs(atr_pct - 1.5) * 5.0
    elif atr_pct < 0.3:
        score = 20.0  # too quiet
    elif atr_pct > 5.0 or atr_ratio > 3.0:
        score = 15.0  # too explosive
    else:
        score = 50.0

    return round(_clamp(score), 4)


def consolidation_score(ohlcv: list, *, bars: int = 20) -> float:
    """Score 0-100 measuring how tight / range-bound price has been recently.

    High score = tight consolidation = potential breakout setup.
    Low score  = trending or volatile = not consolidating.
    """
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 5]
    if len(rows) < bars + 1:
        return 0.0

    recent = rows[-bars:]
    closes = [_safe(r[4]) for r in recent]
    highs  = [_safe(r[2]) for r in recent]
    lows   = [_safe(r[3]) for r in recent]

    avg_close = sum(closes) / len(closes) if closes else 0.0
    if avg_close <= 0:
        return 0.0

    price_range_pct = (max(highs) - min(lows)) / avg_close * 100.0

    # Tighter range = higher score
    if price_range_pct <= 1.5:
        score = 90.0
    elif price_range_pct <= 3.0:
        score = 70.0
    elif price_range_pct <= 6.0:
        score = 50.0
    elif price_range_pct <= 12.0:
        score = 25.0
    else:
        score = 5.0

    return round(_clamp(score), 4)


def spread_quality_score(ohlcv: list, *, bars: int = 10) -> float:
    """Estimate bid-ask spread quality from OHLCV candle shapes.

    Uses (high - low) / close as a proxy for intrabar spread.
    Lower intrabar spread = higher quality = higher score.
    Returns 50 when insufficient data.
    """
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 5]
    if len(rows) < bars:
        return 50.0

    recent = rows[-bars:]
    ratios = []
    for r in recent:
        h, l, c = _safe(r[2]), _safe(r[3]), _safe(r[4])
        if c > 0 and h >= l:
            ratios.append((h - l) / c * 100.0)

    if not ratios:
        return 50.0

    avg_spread_pct = sum(ratios) / len(ratios)

    # Tighter = better
    if avg_spread_pct <= 0.3:
        score = 95.0
    elif avg_spread_pct <= 0.8:
        score = 80.0
    elif avg_spread_pct <= 2.0:
        score = 60.0
    elif avg_spread_pct <= 5.0:
        score = 35.0
    else:
        score = 10.0

    return round(_clamp(score), 4)


def trend_quality_score(ohlcv: list, *, bars: int = 30, sma_period: int = 20) -> float:
    """Score 0-100 measuring how cleanly trending price is (ADX-style proxy).

    High score = clean directional trend.
    Low score  = choppy / mean-reverting price action.
    """
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 5]
    if len(rows) < max(bars, sma_period) + 5:
        return 50.0

    closes = [_safe(r[4]) for r in rows[-bars:]]
    sma = _sma(closes, sma_period)
    if sma is None or sma <= 0:
        return 50.0

    cur = closes[-1]
    # Fraction of bars on the "right side" of SMA
    above = sum(1 for c in closes if c > sma)
    consistency = above / len(closes)

    # Directional distance from SMA
    direction_pct = abs(cur - sma) / sma * 100.0

    trend_score = (consistency * 60.0) + min(direction_pct * 4.0, 40.0)
    return round(_clamp(trend_score), 4)


def illiquidity_risk_score_v2(ohlcv: list, *, baseline_bars: int = 20) -> float:
    """Improved illiquidity/manipulation risk model.

    Considers:
      - Average daily notional (volume * price)
      - Volume consistency (low consistency = manipulation risk)
      - Volatility spikes (sudden extreme candles)

    Returns 0 (safe) to 100 (high risk).
    """
    rows = [r for r in list(ohlcv or []) if isinstance(r, (list, tuple)) and len(r) >= 6]
    if len(rows) < baseline_bars:
        return 100.0

    recent = rows[-baseline_bars:]
    closes = [_safe(r[4]) for r in recent]
    vols   = [_safe(r[5]) for r in recent]
    highs  = [_safe(r[2]) for r in recent]
    lows   = [_safe(r[3]) for r in recent]

    avg_close = sum(closes) / len(closes) if closes else 0.0
    avg_vol   = sum(vols)   / len(vols)   if vols   else 0.0
    notional  = avg_close * avg_vol

    # Base notional risk
    if notional <= 0:
        base_risk = 100.0
    elif notional >= 1_000_000:
        base_risk = 0.0
    elif notional >= 250_000:
        base_risk = 15.0
    elif notional >= 100_000:
        base_risk = 30.0
    elif notional >= 25_000:
        base_risk = 55.0
    else:
        base_risk = 80.0

    # Volume consistency penalty — high variance = more risk
    if avg_vol > 0 and len(vols) >= 5:
        vol_std = (sum((v - avg_vol) ** 2 for v in vols) / len(vols)) ** 0.5
        vol_cv = vol_std / avg_vol  # coefficient of variation
        vol_penalty = min(vol_cv * 20.0, 20.0)
    else:
        vol_penalty = 10.0

    # Extreme candle spike penalty
    spike_penalty = 0.0
    if avg_close > 0:
        for h, l in zip(highs, lows):
            candle_range_pct = (h - l) / avg_close * 100.0
            if candle_range_pct > 15.0:
                spike_penalty += 5.0
        spike_penalty = min(spike_penalty, 20.0)

    total = base_risk + vol_penalty + spike_penalty
    return round(_clamp(total), 4)
