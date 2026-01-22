from __future__ import annotations

from typing import List

def ema(series: List[float], period: int) -> List[float]:
    p = int(period)
    if p <= 1 or len(series) == 0:
        return list(series)
    k = 2.0 / (p + 1.0)
    out = []
    prev = float(series[0])
    out.append(prev)
    for x in series[1:]:
        x = float(x)
        prev = (x * k) + (prev * (1.0 - k))
        out.append(prev)
    return out

def sma(series: List[float], period: int) -> List[float]:
    p = int(period)
    if p <= 1 or len(series) == 0:
        return list(series)
    out = []
    s = 0.0
    q = []
    for x in series:
        x = float(x)
        q.append(x)
        s += x
        if len(q) > p:
            s -= q.pop(0)
        out.append(s / len(q))
    return out

def rsi_wilder(series: List[float], period: int = 14) -> List[float]:
    p = int(period)
    if p <= 1 or len(series) < 2:
        return [50.0 for _ in series]

    gains = []
    losses = []
    for i in range(1, len(series)):
        d = float(series[i]) - float(series[i-1])
        gains.append(max(0.0, d))
        losses.append(max(0.0, -d))

    # initial averages (simple)
    avg_gain = sum(gains[:p]) / p if len(gains) >= p else sum(gains) / max(1, len(gains))
    avg_loss = sum(losses[:p]) / p if len(losses) >= p else sum(losses) / max(1, len(losses))

    out = [50.0]  # align with series length; first value placeholder
    # build first RSI
    rs = (avg_gain / avg_loss) if avg_loss > 1e-12 else 999.0
    out.append(100.0 - (100.0 / (1.0 + rs)))

    # wilder smoothing
    for i in range(p, len(gains)):
        g = gains[i]
        l = losses[i]
        avg_gain = (avg_gain * (p - 1) + g) / p
        avg_loss = (avg_loss * (p - 1) + l) / p
        rs = (avg_gain / avg_loss) if avg_loss > 1e-12 else 999.0
        r = 100.0 - (100.0 / (1.0 + rs))
        out.append(r)

    # pad if needed
    while len(out) < len(series):
        out.append(out[-1] if out else 50.0)
    return out[:len(series)]

def donchian(highs: List[float], lows: List[float], period: int) -> tuple[list[float], list[float]]:
    p = int(period)
    if p <= 1 or len(highs) == 0 or len(lows) == 0:
        return list(highs), list(lows)
    up = []
    dn = []
    for i in range(len(highs)):
        lo = max(0, i - p + 1)
        up.append(max(float(x) for x in highs[lo:i+1]))
        dn.append(min(float(x) for x in lows[lo:i+1]))
    return up, dn
