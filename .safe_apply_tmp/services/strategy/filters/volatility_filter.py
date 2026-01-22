from __future__ import annotations

from services.strategy.signals import Signal
from services.strategy.indicators import atr

def allow(ohlcv: list[list[float]], *, period: int = 14, min_atr_pct: float = 0.05, max_atr_pct: float = 5.0) -> tuple[bool, dict]:
    if not ohlcv or len(ohlcv) < int(period) + 5:
        return (False, {"reason": "insufficient_ohlcv"})
    closes = [float(r[4]) for r in ohlcv]
    a = atr(ohlcv, int(period))
    if not a:
        return (False, {"reason": "atr_failed"})
    atr_now = float(a[-1])
    close = float(closes[-1]) if closes else 0.0
    atr_pct = (atr_now / close * 100.0) if close > 0 else 0.0
    ok = (atr_pct >= float(min_atr_pct)) and (atr_pct <= float(max_atr_pct))
    return (ok, {"atr": atr_now, "atr_pct": atr_pct, "period": period, "min_atr_pct": min_atr_pct, "max_atr_pct": max_atr_pct, "reason": ("ok" if ok else "atr_pct_out_of_band")})
