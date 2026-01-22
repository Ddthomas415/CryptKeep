from __future__ import annotations

from services.strategy.indicators import ema

def allow_for_action(ohlcv: list[list[float]], *, action: str, slow: int = 50, slope_lookback: int = 5) -> tuple[bool, dict]:
    if not ohlcv or len(ohlcv) < int(slow) + int(slope_lookback) + 5:
        return (False, {"reason": "insufficient_ohlcv"})
    closes = [float(r[4]) for r in ohlcv]
    es = ema(closes, int(slow))
    if len(es) < slope_lookback + 2:
        return (False, {"reason": "ema_failed"})
    # slope over last N
    s0 = float(es[-(slope_lookback+1)])
    s1 = float(es[-1])
    slope = s1 - s0
    # Allow BUY only if slope positive; SELL only if slope negative
    if str(action).upper() == "BUY":
        ok = slope > 0
    elif str(action).upper() == "SELL":
        ok = slope < 0
    else:
        ok = True
    return (ok, {"slow": slow, "slope_lookback": slope_lookback, "ema_slow_now": s1, "ema_slow_then": s0, "slope": slope, "reason": ("ok" if ok else "trend_mismatch")})
