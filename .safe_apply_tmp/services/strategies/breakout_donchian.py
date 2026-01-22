from __future__ import annotations

from services.strategies.indicators import donchian

def signal_from_ohlcv(
    *,
    ohlcv: list,
    donchian_len: int = 20,
) -> dict:
    if not ohlcv or len(ohlcv) < 5:
        return {"ok": False, "action": "hold", "reason": "insufficient_ohlcv"}

    highs = [float(r[2]) for r in ohlcv if r and len(r) >= 6]
    lows  = [float(r[3]) for r in ohlcv if r and len(r) >= 6]
    closes= [float(r[4]) for r in ohlcv if r and len(r) >= 6]
    if len(closes) < int(donchian_len) + 2:
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    up, dn = donchian(highs, lows, int(donchian_len))

    # Use "previous channel" to avoid looking at current bar extremes
    upper_prev = float(up[-2])
    lower_prev = float(dn[-2])
    c = float(closes[-1])

    if c > upper_prev:
        return {"ok": True, "action": "buy", "reason": "donchian_break_up", "ind": {"upper_prev": upper_prev, "lower_prev": lower_prev, "close": c}}
    if c < lower_prev:
        return {"ok": True, "action": "sell", "reason": "donchian_break_down", "ind": {"upper_prev": upper_prev, "lower_prev": lower_prev, "close": c}}

    return {"ok": True, "action": "hold", "reason": "inside_channel", "ind": {"upper_prev": upper_prev, "lower_prev": lower_prev, "close": c}}
