from __future__ import annotations

from services.strategies.indicators import rsi_wilder, sma

def signal_from_ohlcv(
    *,
    ohlcv: list,
    rsi_len: int = 14,
    rsi_buy: float = 30.0,
    rsi_sell: float = 70.0,
    sma_len: int = 50,
) -> dict:
    if not ohlcv or len(ohlcv) < 5:
        return {"ok": False, "action": "hold", "reason": "insufficient_ohlcv"}

    closes = [float(r[4]) for r in ohlcv if r and len(r) >= 6]
    if len(closes) < max(int(rsi_len) + 2, int(sma_len) + 2):
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    rsi = rsi_wilder(closes, int(rsi_len))
    ma = sma(closes, int(sma_len))
    c = closes[-1]
    r = float(rsi[-1])
    m = float(ma[-1])

    # Conservative mean reversion filter: buy only when below SMA; sell only when above SMA
    if r <= float(rsi_buy) and c <= m:
        return {"ok": True, "action": "buy", "reason": "rsi_oversold_below_sma", "ind": {"rsi": r, "sma": m, "close": c}}
    if r >= float(rsi_sell) and c >= m:
        return {"ok": True, "action": "sell", "reason": "rsi_overbought_above_sma", "ind": {"rsi": r, "sma": m, "close": c}}

    return {"ok": True, "action": "hold", "reason": "no_edge", "ind": {"rsi": r, "sma": m, "close": c}}
