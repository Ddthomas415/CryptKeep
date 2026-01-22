from __future__ import annotations

from services.strategy.signals import Signal, hold, bad
from services.strategy.indicators import ema

def compute(ohlcv: list[list[float]], *, fast: int = 12, slow: int = 26) -> Signal:
    if not ohlcv or len(ohlcv) < max(fast, slow) + 3:
        return bad("insufficient_ohlcv")
    closes = [float(r[4]) for r in ohlcv if len(r) >= 5]
    if len(closes) < max(fast, slow) + 3:
        return bad("insufficient_closes")

    ef = ema(closes, int(fast))
    es = ema(closes, int(slow))
    f_prev, f_now = ef[-2], ef[-1]
    s_prev, s_now = es[-2], es[-1]
    ts_ms = int(ohlcv[-1][0])
    close = closes[-1]

    if f_prev <= s_prev and f_now > s_now:
        return Signal(ok=True, action="BUY", reason="fast_crossed_above_slow", confidence=0.65, ts_ms=ts_ms, close=close,
                      features={"ema_fast": f_now, "ema_slow": s_now, "fast": fast, "slow": slow})
    if f_prev >= s_prev and f_now < s_now:
        return Signal(ok=True, action="SELL", reason="fast_crossed_below_slow", confidence=0.65, ts_ms=ts_ms, close=close,
                      features={"ema_fast": f_now, "ema_slow": s_now, "fast": fast, "slow": slow})
    return hold("no_cross", ts_ms=ts_ms, close=close, features={"ema_fast": f_now, "ema_slow": s_now, "fast": fast, "slow": slow})
