from __future__ import annotations

from services.strategies.indicators import donchian
from services.strategies.market_filters import market_context, pct_gap

def signal_from_ohlcv(
    *,
    ohlcv: list,
    donchian_len: int = 20,
    filter_window: int | None = None,
    min_volatility_pct: float | None = None,
    min_volume_ratio: float | None = None,
    min_trend_efficiency: float | None = None,
    min_channel_width_pct: float | None = None,
    breakout_buffer_pct: float | None = None,
    require_directional_confirmation: bool = False,
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

    buffer_frac = max(0.0, float(breakout_buffer_pct or 0.0)) / 100.0
    action = "hold"
    reason = "inside_channel"
    if c > upper_prev * (1.0 + buffer_frac):
        action = "buy"
        reason = "donchian_break_up"
    elif c < lower_prev * (1.0 - buffer_frac):
        action = "sell"
        reason = "donchian_break_down"

    ctx = market_context(ohlcv=ohlcv, window=int(filter_window or max(donchian_len, 8)))
    channel_width_pct = pct_gap(upper_prev, lower_prev, base=c)
    ind = {
        "upper_prev": upper_prev,
        "lower_prev": lower_prev,
        "close": c,
        "avg_range_pct": ctx["avg_range_pct"],
        "volume_ratio": ctx["volume_ratio"],
        "trend_efficiency": ctx["trend_efficiency"],
        "channel_width_pct": channel_width_pct,
    }

    if action == "hold":
        return {"ok": True, "action": action, "reason": reason, "ind": ind}

    if min_volatility_pct is not None and ctx["avg_range_pct"] < float(min_volatility_pct):
        return {"ok": True, "action": "hold", "reason": "low_volatility_filter", "ind": ind}
    if min_volume_ratio is not None and ctx["volume_ratio"] < float(min_volume_ratio):
        return {"ok": True, "action": "hold", "reason": "low_volume_filter", "ind": ind}
    if min_trend_efficiency is not None and ctx["trend_efficiency"] < float(min_trend_efficiency):
        return {"ok": True, "action": "hold", "reason": "chop_filter", "ind": ind}
    if min_channel_width_pct is not None and channel_width_pct < float(min_channel_width_pct):
        return {"ok": True, "action": "hold", "reason": "narrow_channel_filter", "ind": ind}
    if require_directional_confirmation and action == "buy" and c < ctx["prev_close"]:
        return {"ok": True, "action": "hold", "reason": "breakout_not_confirmed", "ind": ind}
    if require_directional_confirmation and action == "sell" and c > ctx["prev_close"]:
        return {"ok": True, "action": "hold", "reason": "breakout_not_confirmed", "ind": ind}

    return {"ok": True, "action": action, "reason": reason, "ind": ind}
