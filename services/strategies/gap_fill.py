from __future__ import annotations

from services.strategies.indicators import rsi_wilder, sma
from services.strategies.market_filters import market_context


def signal_from_ohlcv(
    *,
    ohlcv: list,
    rsi_len: int = 14,
    rsi_buy: float = 40.0,
    rsi_sell: float = 60.0,
    sma_len: int = 20,
    filter_window: int | None = None,
    min_gap_pct: float = 3.0,
    gap_fill_target_pct: float = 0.618,
    min_volume_ratio: float | None = None,
) -> dict:
    """
    Gap fill strategy: when price gaps down at open, bet on partial fill back up.

    Entry (buy):
    - Today's open is >= min_gap_pct below yesterday's close (gap down)
    - RSI is not already overbought
    - Price is still below yesterday's close (gap not yet filled)

    Exit (sell):
    - Price fills gap_fill_target_pct of the gap (default 61.8%)
    - Or RSI hits rsi_sell
    """
    if not ohlcv or len(ohlcv) < 5:
        return {"ok": False, "action": "hold", "reason": "insufficient_ohlcv"}

    opens   = [float(r[1]) for r in ohlcv if r and len(r) >= 6]
    closes  = [float(r[4]) for r in ohlcv if r and len(r) >= 6]

    need = max(int(rsi_len) + 2, int(sma_len) + 2, 3)
    if len(closes) < need:
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    rsi_series   = rsi_wilder(closes, int(rsi_len))
    ma_series    = sma(closes, int(sma_len))
    cur_rsi      = float(rsi_series[-1])
    cur_ma       = float(ma_series[-1])
    cur_close    = closes[-1]
    cur_open     = opens[-1]
    prev_close   = closes[-2]

    # Gap calculation: gap_pct is negative for gap down
    gap_pct = ((cur_open - prev_close) / prev_close * 100.0) if prev_close > 0 else 0.0
    gap_size = prev_close - cur_open  # positive = gap down

    # How much of the gap has been filled so far
    filled_pct = ((cur_close - cur_open) / gap_size) if gap_size > 1e-10 else 0.0
    fill_target = prev_close - (gap_size * (1.0 - float(gap_fill_target_pct)))

    ctx = market_context(ohlcv=ohlcv, window=int(filter_window or max(sma_len, rsi_len, 8)))

    ind = {
        "rsi":          round(cur_rsi, 1),
        "sma":          round(cur_ma, 6),
        "close":        round(cur_close, 6),
        "open":         round(cur_open, 6),
        "prev_close":   round(prev_close, 6),
        "gap_pct":      round(gap_pct, 2),
        "gap_size":     round(gap_size, 6),
        "filled_pct":   round(filled_pct, 3),
        "fill_target":  round(fill_target, 6),
        "avg_range_pct":ctx["avg_range_pct"],
        "volume_ratio": ctx["volume_ratio"],
        "trend_efficiency": ctx["trend_efficiency"],
    }

    # EXIT: gap filled to target or RSI overbought
    if cur_rsi >= float(rsi_sell):
        return {"ok": True, "action": "sell", "reason": "rsi_exit", "ind": ind}
    if gap_size > 0 and cur_close >= fill_target:
        return {"ok": True, "action": "sell", "reason": "gap_fill_target_reached", "ind": ind}

    # ENTRY: gap down of sufficient size, not yet filled, RSI not overbought
    gap_down     = gap_pct <= -abs(float(min_gap_pct))
    not_filled   = cur_close < prev_close
    rsi_ok       = cur_rsi < float(rsi_buy)

    if gap_down and not_filled and rsi_ok:
        if min_volume_ratio is not None and ctx["volume_ratio"] < float(min_volume_ratio):
            return {"ok": True, "action": "hold", "reason": "low_volume_filter", "ind": ind}
        return {"ok": True, "action": "buy", "reason": "gap_fill_entry", "ind": ind}

    reasons = []
    if not gap_down:   reasons.append(f"gap_pct={gap_pct:.1f}%>={-min_gap_pct}%")
    if not not_filled: reasons.append("gap_already_filled")
    if not rsi_ok:     reasons.append(f"rsi={cur_rsi:.0f}>={rsi_buy}")

    return {"ok": True, "action": "hold", "reason": "filters_failed:" + ",".join(reasons), "ind": ind}
