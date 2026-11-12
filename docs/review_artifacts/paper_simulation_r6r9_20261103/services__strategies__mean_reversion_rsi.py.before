from __future__ import annotations

from services.strategies.indicators import rsi_wilder, sma
from services.strategies.market_filters import market_context, pct_gap

def signal_from_ohlcv(
    *,
    ohlcv: list,
    rsi_len: int = 14,
    rsi_buy: float = 30.0,
    rsi_sell: float = 70.0,
    sma_len: int = 50,
    filter_window: int | None = None,
    max_volatility_pct: float | None = None,
    min_volume_ratio: float | None = None,
    max_trend_efficiency: float | None = None,
    max_sma_distance_pct: float | None = None,
    require_reversal_confirmation: bool = False,
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

    action = "hold"
    reason = "no_edge"
    if r <= float(rsi_buy) and c <= m:
        action = "buy"
        reason = "rsi_oversold_below_sma"
    elif r >= float(rsi_sell) and c >= m:
        action = "sell"
        reason = "rsi_overbought_above_sma"

    ctx = market_context(ohlcv=ohlcv, window=int(filter_window or max(sma_len, rsi_len, 8)))
    sma_distance_pct = pct_gap(c, m, base=c)
    ind = {
        "rsi": r,
        "sma": m,
        "close": c,
        "avg_range_pct": ctx["avg_range_pct"],
        "volume_ratio": ctx["volume_ratio"],
        "trend_efficiency": ctx["trend_efficiency"],
        "sma_distance_pct": sma_distance_pct,
    }

    if action == "hold":
        return {"ok": True, "action": action, "reason": reason, "ind": ind}

    if max_volatility_pct is not None and ctx["avg_range_pct"] > float(max_volatility_pct):
        return {"ok": True, "action": "hold", "reason": "high_volatility_filter", "ind": ind}
    if min_volume_ratio is not None and ctx["volume_ratio"] < float(min_volume_ratio):
        return {"ok": True, "action": "hold", "reason": "low_volume_filter", "ind": ind}
    if max_trend_efficiency is not None and ctx["trend_efficiency"] > float(max_trend_efficiency):
        return {"ok": True, "action": "hold", "reason": "one_way_trend_filter", "ind": ind}
    if max_sma_distance_pct is not None and sma_distance_pct > float(max_sma_distance_pct):
        return {"ok": True, "action": "hold", "reason": "reversion_invalidation", "ind": ind}
    if require_reversal_confirmation and action == "buy" and c < ctx["prev_close"]:
        return {"ok": True, "action": "hold", "reason": "reversal_not_confirmed", "ind": ind}
    if require_reversal_confirmation and action == "sell" and c > ctx["prev_close"]:
        return {"ok": True, "action": "hold", "reason": "reversal_not_confirmed", "ind": ind}

    return {"ok": True, "action": action, "reason": reason, "ind": ind}
