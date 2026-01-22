from __future__ import annotations

from typing import List, Optional

def ema(values: list[float], period: int) -> list[float]:
    if period <= 1:
        return values[:]
    k = 2 / (period + 1)
    out: list[float] = []
    e = None
    for v in values:
        if e is None:
            e = v
        else:
            e = (v * k) + (e * (1 - k))
        out.append(float(e))
    return out

def sma(values: list[float], period: int) -> list[float]:
    if period <= 1:
        return values[:]
    out: list[float] = []
    s = 0.0
    q: list[float] = []
    for v in values:
        q.append(float(v))
        s += float(v)
        if len(q) > period:
            s -= q.pop(0)
        out.append(s / len(q))
    return out

def std(values: list[float], period: int) -> list[float]:
    if period <= 1:
        return [0.0 for _ in values]
    out: list[float] = []
    q: list[float] = []
    for v in values:
        q.append(float(v))
        if len(q) > period:
            q.pop(0)
        m = sum(q) / len(q)
        var = sum((x - m) ** 2 for x in q) / max(1, (len(q) - 1))
        out.append(var ** 0.5)
    return out

def atr(ohlcv: list[list[float]], period: int) -> list[float]:
    # ohlcv rows: [ms, open, high, low, close, volume]
    if not ohlcv:
        return []
    highs = [float(r[2]) for r in ohlcv]
    lows  = [float(r[3]) for r in ohlcv]
    closes= [float(r[4]) for r in ohlcv]
    trs: list[float] = []
    prev_close = closes[0]
    for h,l,c in zip(highs, lows, closes):
        tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        trs.append(float(tr))
        prev_close = c
    # ATR = EMA of TR (common)
    return ema(trs, int(period))
