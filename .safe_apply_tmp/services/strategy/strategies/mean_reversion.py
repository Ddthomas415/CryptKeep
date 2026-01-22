from __future__ import annotations

from services.strategy.signals import Signal, hold, bad
from services.strategy.indicators import sma, std

def compute(ohlcv: list[list[float]], *, lookback: int = 50, entry_z: float = 2.0) -> Signal:
    if not ohlcv or len(ohlcv) < int(lookback) + 5:
        return bad("insufficient_ohlcv")
    closes = [float(r[4]) for r in ohlcv if len(r) >= 5]
    if len(closes) < int(lookback) + 5:
        return bad("insufficient_closes")

    ma = sma(closes, int(lookback))
    sd = std(closes, int(lookback))
    ts_ms = int(ohlcv[-1][0])
    close = closes[-1]
    m = ma[-1]
    s = sd[-1] if sd[-1] > 1e-12 else 1e-12
    z = (close - m) / s

    # Simple symmetric MR: buy when far below mean, sell when far above mean
    if z <= -float(entry_z):
        conf = min(0.9, 0.55 + (abs(z) / (abs(entry_z) + 1e-9)) * 0.15)
        return Signal(ok=True, action="BUY", reason="zscore_low", confidence=conf, ts_ms=ts_ms, close=close,
                      features={"z": z, "ma": m, "sd": s, "lookback": lookback, "entry_z": entry_z})
    if z >= float(entry_z):
        conf = min(0.9, 0.55 + (abs(z) / (abs(entry_z) + 1e-9)) * 0.15)
        return Signal(ok=True, action="SELL", reason="zscore_high", confidence=conf, ts_ms=ts_ms, close=close,
                      features={"z": z, "ma": m, "sd": s, "lookback": lookback, "entry_z": entry_z})
    return hold("zscore_neutral", ts_ms=ts_ms, close=close, features={"z": z, "ma": m, "sd": s, "lookback": lookback, "entry_z": entry_z})
