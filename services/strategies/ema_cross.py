from __future__ import annotations

from services.strategies.indicators import ema

def signal_from_ohlcv(*, ohlcv: list, ema_fast: int = 12, ema_slow: int = 26) -> dict:
    if not ohlcv or len(ohlcv) < 5:
        return {"ok": False, "action": "hold", "reason": "insufficient_ohlcv"}

    closes = [float(r[4]) for r in ohlcv if r and len(r) >= 6]
    if len(closes) < max(int(ema_fast), int(ema_slow)) + 2:
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    ef = ema(closes, int(ema_fast))
    es = ema(closes, int(ema_slow))

    # cross detection using last two points
    prev = (ef[-2] - es[-2])
    cur = (ef[-1] - es[-1])

    if prev <= 0 and cur > 0:
        return {"ok": True, "action": "buy", "reason": "ema_cross_up", "ind": {"ema_fast": ef[-1], "ema_slow": es[-1]}}
    if prev >= 0 and cur < 0:
        return {"ok": True, "action": "sell", "reason": "ema_cross_down", "ind": {"ema_fast": ef[-1], "ema_slow": es[-1]}}

    return {"ok": True, "action": "hold", "reason": "no_cross", "ind": {"ema_fast": ef[-1], "ema_slow": es[-1]}}
