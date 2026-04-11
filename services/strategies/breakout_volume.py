from __future__ import annotations

from services.strategies.indicators import donchian, sma
from services.strategies.market_filters import market_context, pct_gap


def signal_from_ohlcv(
    *,
    ohlcv: list,
    donchian_len: int = 20,
    sma_len: int = 50,
    filter_window: int | None = None,
    min_volume_ratio: float = 2.0,
    min_volatility_pct: float | None = None,
    min_trend_efficiency: float | None = None,
    breakout_buffer_pct: float = 0.1,
    min_channel_width_pct: float = 1.0,
    require_close_above: bool = True,
) -> dict:
    """
    Breakout on volume confirmation.

    Entry (buy):
    - Price closes above Donchian upper band
    - Volume is >= min_volume_ratio x recent average (confirmed move)
    - Channel is wide enough to be meaningful

    Entry (sell):
    - Price closes below Donchian lower band with volume confirmation

    This differs from plain Donchian: volume must confirm the breakout.
    Without volume, breakouts are ignored as false breaks.
    """
    if not ohlcv or len(ohlcv) < 5:
        return {"ok": False, "action": "hold", "reason": "insufficient_ohlcv"}

    closes  = [float(r[4]) for r in ohlcv if r and len(r) >= 6]
    highs   = [float(r[2]) for r in ohlcv if r and len(r) >= 6]
    lows    = [float(r[3]) for r in ohlcv if r and len(r) >= 6]

    need = max(int(donchian_len) + 2, int(sma_len) + 2)
    if len(closes) < need:
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    # Use prior bar's Donchian to avoid lookahead
    upper_series, lower_series = donchian(highs[:-1], lows[:-1], int(donchian_len))
    ma_series = sma(closes, int(sma_len))

    upper   = float(upper_series[-1])
    lower   = float(lower_series[-1])
    cur_ma  = float(ma_series[-1])
    cur     = closes[-1]

    channel_width_pct = ((upper - lower) / cur * 100.0) if cur > 0 else 0.0
    buf_upper = upper * (1.0 + float(breakout_buffer_pct) / 100.0)
    buf_lower = lower * (1.0 - float(breakout_buffer_pct) / 100.0)

    ctx = market_context(ohlcv=ohlcv, window=int(filter_window or max(donchian_len, 8)))

    ind = {
        "close":             round(cur, 6),
        "donchian_upper":    round(upper, 6),
        "donchian_lower":    round(lower, 6),
        "channel_width_pct": round(channel_width_pct, 2),
        "sma":               round(cur_ma, 6),
        "avg_range_pct":     ctx["avg_range_pct"],
        "volume_ratio":      ctx["volume_ratio"],
        "trend_efficiency":  ctx["trend_efficiency"],
    }

    # Channel too narrow to be meaningful
    if channel_width_pct < float(min_channel_width_pct):
        return {"ok": True, "action": "hold", "reason": "channel_too_narrow", "ind": ind}

    # Volume confirmation check — THIS is what makes this different from plain Donchian
    volume_confirmed = ctx["volume_ratio"] >= float(min_volume_ratio)

    if not volume_confirmed:
        return {"ok": True, "action": "hold", "reason": f"breakout_no_volume_confirmation:ratio={ctx['volume_ratio']:.2f}<{min_volume_ratio}", "ind": ind}

    action = "hold"
    reason = "no_breakout"

    close_above = cur > buf_upper if bool(require_close_above) else cur >= upper
    close_below = cur < buf_lower if bool(require_close_above) else cur <= lower

    if close_above:
        action = "buy"
        reason = "volume_confirmed_breakout_up"
    elif close_below:
        action = "sell"
        reason = "volume_confirmed_breakout_down"

    if action == "hold":
        return {"ok": True, "action": action, "reason": reason, "ind": ind}

    # Additional filters
    if min_volatility_pct is not None and ctx["avg_range_pct"] < float(min_volatility_pct):
        return {"ok": True, "action": "hold", "reason": "low_volatility_filter", "ind": ind}
    if min_trend_efficiency is not None and ctx["trend_efficiency"] < float(min_trend_efficiency):
        return {"ok": True, "action": "hold", "reason": "chop_filter", "ind": ind}

    return {"ok": True, "action": action, "reason": reason, "ind": ind}
