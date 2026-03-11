from __future__ import annotations

from services.strategies.indicators import ema


def _ema_pair_from_closes(closes: list[float], *, ema_fast: int, ema_slow: int) -> tuple[float, float, float, float] | None:
    if len(closes) < max(int(ema_fast), int(ema_slow)) + 2:
        return None
    ef = ema(closes, int(ema_fast))
    es = ema(closes, int(ema_slow))
    return float(ef[-2]), float(ef[-1]), float(es[-2]), float(es[-1])


def signal_from_ohlcv(*, ohlcv: list, ema_fast: int = 12, ema_slow: int = 26) -> dict:
    if not ohlcv or len(ohlcv) < 5:
        return {"ok": False, "action": "hold", "reason": "insufficient_ohlcv"}

    closes = [float(r[4]) for r in ohlcv if r and len(r) >= 6]
    pair = _ema_pair_from_closes(closes, ema_fast=int(ema_fast), ema_slow=int(ema_slow))
    if pair is None:
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    # cross detection using last two points
    ef_prev, ef_cur, es_prev, es_cur = pair
    prev = (ef_prev - es_prev)
    cur = (ef_cur - es_cur)

    if prev <= 0 and cur > 0:
        return {"ok": True, "action": "buy", "reason": "ema_cross_up", "ind": {"ema_fast": ef_cur, "ema_slow": es_cur}}
    if prev >= 0 and cur < 0:
        return {"ok": True, "action": "sell", "reason": "ema_cross_down", "ind": {"ema_fast": ef_cur, "ema_slow": es_cur}}

    return {"ok": True, "action": "hold", "reason": "no_cross", "ind": {"ema_fast": ef_cur, "ema_slow": es_cur}}


def ema_crossover_signal(*, closes: list[float], fast: int = 12, slow: int = 26) -> dict:
    """Compatibility wrapper expected by legacy strategy adapters."""
    series = [float(x) for x in (closes or [])]
    pair = _ema_pair_from_closes(series, ema_fast=int(fast), ema_slow=int(slow))
    if pair is None:
        return {
            "ok": False,
            "reason": "insufficient_history",
            "signal": "hold",
            "fast_ema": None,
            "slow_ema": None,
            "cross_up": False,
            "cross_down": False,
        }

    ef_prev, ef_cur, es_prev, es_cur = pair
    prev = ef_prev - es_prev
    cur = ef_cur - es_cur
    cross_up = prev <= 0 and cur > 0
    cross_down = prev >= 0 and cur < 0

    if cross_up:
        signal = "buy"
    elif cross_down:
        signal = "sell"
    else:
        signal = "hold"

    return {
        "ok": True,
        "signal": signal,
        "fast_ema": float(ef_cur),
        "slow_ema": float(es_cur),
        "cross_up": bool(cross_up),
        "cross_down": bool(cross_down),
    }
