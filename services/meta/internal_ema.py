from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import math
from services.backtest.signal_replay import fetch_ohlcv

def _ema(values: list[float], period: int) -> list[float]:
    if period <= 1:
        return values[:]
    k = 2.0 / (period + 1.0)
    out = []
    ema = None
    for v in values:
        if ema is None:
            ema = v
        else:
            ema = (v - ema) * k + ema
        out.append(ema)
    return out

def ema_crossover_signal(venue: str, symbol: str, timeframe: str, fast: int, slow: int, limit: int = 300) -> dict:
    ohlcv = fetch_ohlcv(venue, symbol, timeframe=timeframe, limit=int(limit))
    if not ohlcv or len(ohlcv) < max(fast, slow) + 5:
        return {"ok": False, "reason": "insufficient_ohlcv", "action": "hold", "score": 0.0, "confidence": 0.0}
    closes = [float(r[4]) for r in ohlcv if r and r[4] is not None]
    if len(closes) < max(fast, slow) + 5:
        return {"ok": False, "reason": "insufficient_closes", "action": "hold", "score": 0.0, "confidence": 0.0}
    ef = _ema(closes, int(fast))
    es = _ema(closes, int(slow))
    f1, f0 = ef[-2], ef[-1]
    s1, s0 = es[-2], es[-1]
    prev_diff = f1 - s1
    diff = f0 - s0
    action = "hold"
    score = 0.0
    if prev_diff <= 0 and diff > 0:
        action = "buy"
        score = 1.0
    elif prev_diff >= 0 and diff < 0:
        action = "sell"
        score = -1.0
    sep = abs(diff) / max(1e-9, abs(s0))
    conf = float(max(0.0, min(1.0, sep * 25.0)))
    return {
        "ok": True,
        "action": action,
        "score": float(score),
        "confidence": float(conf),
        "meta": {
            "fast": int(fast),
            "slow": int(slow),
            "ema_fast": float(f0),
            "ema_slow": float(s0),
            "sep": float(sep),
        }
    }
