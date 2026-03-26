from __future__ import annotations

from services.strategies.indicators import ema
from services.strategies.market_filters import market_context, pct_gap
from services.strategy_runner.strategies.ema_crossover import (
    EMACfg,
    EMAState,
    update_ema_state,
    compute_signal as canonical_compute_signal,
)


def _ema_pair_from_closes(closes: list[float], *, ema_fast: int, ema_slow: int) -> tuple[float, float, float, float] | None:
    if len(closes) < max(int(ema_fast), int(ema_slow)) + 2:
        return None
    ef = ema(closes, int(ema_fast))
    es = ema(closes, int(ema_slow))
    return float(ef[-2]), float(ef[-1]), float(es[-2]), float(es[-1])


def signal_from_ohlcv(ohlcv, ema_fast=12, ema_slow=26, **kwargs):
    closes = [float(r[4]) for r in ohlcv]
    need = max(int(ema_fast), int(ema_slow)) + 2
    if not ohlcv or len(ohlcv) < 5:
        return {"ok": False, "action": "hold", "reason": "insufficient_ohlcv"}
    if len(closes) < need:
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    cfg = EMACfg(
        fast=int(ema_fast),
        slow=int(ema_slow),
        min_history=need,
    )
    st = EMAState()
    for px in closes:
        st = update_ema_state(float(px), cfg, st)
    signal_code = canonical_compute_signal(st)
    pair = _ema_pair_from_closes(closes, ema_fast=int(ema_fast), ema_slow=int(ema_slow))
    if pair is None:
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    ef_prev, ef_cur, es_prev, es_cur = pair
    prev_gap = ef_prev - es_prev
    cur_gap = ef_cur - es_cur

    action = "hold"
    reason = "no_cross"
    if signal_code > 0 and prev_gap <= 0.0 and cur_gap > 0.0:
        action = "buy"
        reason = "ema_cross_up"
    elif signal_code < 0 and prev_gap >= 0.0 and cur_gap < 0.0:
        action = "sell"
        reason = "ema_cross_down"

    filter_window = kwargs.get("filter_window")
    ctx = market_context(ohlcv=ohlcv, window=int(filter_window or max(ema_slow, ema_fast, 8)))
    cross_gap_pct = pct_gap(ef_cur, es_cur, base=ctx["close"] or closes[-1])
    ind = {
        "ema_fast": float(ef_cur),
        "ema_slow": float(es_cur),
        "avg_range_pct": ctx["avg_range_pct"],
        "volume_ratio": ctx["volume_ratio"],
        "trend_efficiency": ctx["trend_efficiency"],
        "cross_gap_pct": cross_gap_pct,
    }

    if action == "hold":
        return {"ok": True, "action": action, "reason": reason, "ind": ind}

    min_volatility_pct = kwargs.get("min_volatility_pct")
    min_volume_ratio = kwargs.get("min_volume_ratio")
    min_trend_efficiency = kwargs.get("min_trend_efficiency")
    min_cross_gap_pct = kwargs.get("min_cross_gap_pct")

    if min_volatility_pct is not None and ctx["avg_range_pct"] < float(min_volatility_pct):
        return {"ok": True, "action": "hold", "reason": "low_volatility_filter", "ind": ind}
    if min_volume_ratio is not None and ctx["volume_ratio"] < float(min_volume_ratio):
        return {"ok": True, "action": "hold", "reason": "low_volume_filter", "ind": ind}
    if min_trend_efficiency is not None and ctx["trend_efficiency"] < float(min_trend_efficiency):
        return {"ok": True, "action": "hold", "reason": "chop_filter", "ind": ind}
    if min_cross_gap_pct is not None and cross_gap_pct < float(min_cross_gap_pct):
        return {"ok": True, "action": "hold", "reason": "cross_gap_filter", "ind": ind}

    return {"ok": True, "action": action, "reason": reason, "ind": ind}

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
