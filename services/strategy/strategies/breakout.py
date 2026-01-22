from __future__ import annotations

from services.strategy.signals import Signal, hold, bad

def compute(ohlcv: list[list[float]], *, lookback: int = 20) -> Signal:
    if not ohlcv or len(ohlcv) < int(lookback) + 5:
        return bad("insufficient_ohlcv")

    highs = [float(r[2]) for r in ohlcv]
    lows  = [float(r[3]) for r in ohlcv]
    closes= [float(r[4]) for r in ohlcv]
    ts_ms = int(ohlcv[-1][0])
    close = closes[-1]

    # Use prior window (exclude current bar) for breakout boundary
    hi = max(highs[-(lookback+1):-1])
    lo = min(lows[-(lookback+1):-1])

    if close > hi:
        return Signal(ok=True, action="BUY", reason="donchian_break_high", confidence=0.65, ts_ms=ts_ms, close=close,
                      features={"lookback": lookback, "donchian_high": hi, "donchian_low": lo})
    if close < lo:
        return Signal(ok=True, action="SELL", reason="donchian_break_low", confidence=0.65, ts_ms=ts_ms, close=close,
                      features={"lookback": lookback, "donchian_high": hi, "donchian_low": lo})
    return hold("inside_donchian", ts_ms=ts_ms, close=close, features={"lookback": lookback, "donchian_high": hi, "donchian_low": lo})
