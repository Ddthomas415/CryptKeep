"""
Regime detection — is the market trending, ranging, or volatile right now?

Uses ADX-style directional movement + volatility to classify:
- trending_up
- trending_down
- ranging (sideways)
- high_volatility
- low_volatility

Used to gate which strategies should fire.
"""
from __future__ import annotations
import math
from typing import Any


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else d
    except Exception:
        return d


def _atr(ohlcv: list, period: int = 14) -> float:
    """Average True Range."""
    if len(ohlcv) < 2:
        return 0.0
    trs = []
    for i in range(1, len(ohlcv)):
        h = _safe(ohlcv[i][2])
        l = _safe(ohlcv[i][3])
        pc = _safe(ohlcv[i-1][4])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    window = trs[-period:]
    return sum(window) / len(window) if window else 0.0


def _dm(ohlcv: list, period: int = 14) -> tuple[float, float]:
    """Directional movement +DM and -DM."""
    if len(ohlcv) < 2:
        return 0.0, 0.0
    pdm, mdm = [], []
    for i in range(1, len(ohlcv)):
        up   = _safe(ohlcv[i][2]) - _safe(ohlcv[i-1][2])
        down = _safe(ohlcv[i-1][3]) - _safe(ohlcv[i][3])
        pdm.append(up   if up > down and up > 0   else 0.0)
        mdm.append(down if down > up and down > 0 else 0.0)
    w = pdm[-period:], mdm[-period:]
    sp = sum(w[0]) / len(w[0]) if w[0] else 0.0
    sm = sum(w[1]) / len(w[1]) if w[1] else 0.0
    return sp, sm


def detect_regime(
    ohlcv: list,
    *,
    period: int = 14,
    adx_trend_threshold: float = 25.0,
    vol_high_threshold: float = 4.0,
    vol_low_threshold: float = 0.5,
) -> dict[str, Any]:
    """
    Classify current market regime from OHLCV data.

    Returns:
        {
            "regime": "trending_up" | "trending_down" | "ranging" | "high_volatility" | "low_volatility",
            "adx": float,
            "atr": float,
            "atr_pct": float,
            "di_plus": float,
            "di_minus": float,
            "trend_direction": "up" | "down" | "flat",
        }
    """
    if not ohlcv or len(ohlcv) < period + 2:
        return {
            "regime": "unknown",
            "adx": 0.0, "atr": 0.0, "atr_pct": 0.0,
            "di_plus": 0.0, "di_minus": 0.0,
            "trend_direction": "flat",
        }

    atr      = _atr(ohlcv, period)
    cur      = _safe(ohlcv[-1][4])
    atr_pct  = (atr / cur * 100.0) if cur > 0 else 0.0
    pdm, mdm = _dm(ohlcv, period)
    di_plus  = (pdm / atr * 100.0) if atr > 0 else 0.0
    di_minus = (mdm / atr * 100.0) if atr > 0 else 0.0
    dx       = abs(di_plus - di_minus) / (di_plus + di_minus) * 100.0 if (di_plus + di_minus) > 0 else 0.0
    adx      = dx  # simplified (true ADX smooths DX over period)

    trend_direction = "flat"
    if di_plus > di_minus:
        trend_direction = "up"
    elif di_minus > di_plus:
        trend_direction = "down"

    if atr_pct >= float(vol_high_threshold):
        regime = "high_volatility"
    elif atr_pct <= float(vol_low_threshold):
        regime = "low_volatility"
    elif adx >= float(adx_trend_threshold):
        regime = "trending_up" if trend_direction == "up" else "trending_down"
    else:
        regime = "ranging"

    return {
        "regime":          regime,
        "adx":             round(adx, 2),
        "atr":             round(atr, 6),
        "atr_pct":         round(atr_pct, 2),
        "di_plus":         round(di_plus, 2),
        "di_minus":        round(di_minus, 2),
        "trend_direction": trend_direction,
    }


# Which strategies work best in each regime
REGIME_STRATEGY_MAP = {
    "trending_up":    ["momentum", "breakout_volume", "ema_cross"],
    "trending_down":  ["volatility_reversal", "mean_reversion_rsi"],
    "ranging":        ["mean_reversion_rsi", "volatility_reversal", "gap_fill"],
    "high_volatility":["volatility_reversal", "gap_fill", "momentum"],
    "low_volatility": ["mean_reversion_rsi", "breakout_donchian"],
    "unknown":        ["ema_cross"],
}


def recommended_strategies(ohlcv: list, **kwargs) -> list[str]:
    """Return list of strategies recommended for current regime."""
    r = detect_regime(ohlcv, **kwargs)
    return REGIME_STRATEGY_MAP.get(r["regime"], ["ema_cross"])
