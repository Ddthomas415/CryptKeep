from __future__ import annotations

from services.strategies.indicators import rsi_wilder, sma
from services.strategies.market_filters import market_context, pct_gap


def signal_from_ohlcv(
    *,
    ohlcv: list,
    rsi_len: int = 14,
    rsi_oversold: float = 28.0,
    rsi_exit: float = 50.0,
    sma_len: int = 20,
    filter_window: int | None = None,
    min_dump_bars: int = 3,
    min_dump_pct: float = 8.0,
    max_volatility_pct: float | None = None,
    min_volume_ratio: float | None = None,
    require_volume_spike: bool = True,
) -> dict:
    """
    Volatility reversal: enter after a sharp multi-bar dump with RSI oversold.

    Entry (buy):
    - Price dropped >= min_dump_pct over min_dump_bars bars
    - RSI < rsi_oversold (deeply oversold)
    - Volume spike on the dump bar (capitulation signal)
    - Price near session low

    Exit (sell):
    - RSI recovers above rsi_exit
    - Or opposite condition triggers
    """
    if not ohlcv or len(ohlcv) < 5:
        return {"ok": False, "action": "hold", "reason": "insufficient_ohlcv"}

    closes  = [float(r[4]) for r in ohlcv if r and len(r) >= 6]
    highs   = [float(r[2]) for r in ohlcv if r and len(r) >= 6]
    lows    = [float(r[3]) for r in ohlcv if r and len(r) >= 6]
    volumes = [float(r[5]) for r in ohlcv if r and len(r) >= 6]

    need = max(int(rsi_len) + 2, int(sma_len) + 2, int(min_dump_bars) + 1)
    if len(closes) < need:
        return {"ok": False, "action": "hold", "reason": "insufficient_history"}

    rsi_series = rsi_wilder(closes, int(rsi_len))
    ma_series  = sma(closes, int(sma_len))
    cur_rsi    = float(rsi_series[-1])
    cur_ma     = float(ma_series[-1])
    cur_close  = closes[-1]
    cur_high   = highs[-1]
    cur_low    = lows[-1]

    # Measure dump over last N bars
    dump_start = closes[-(int(min_dump_bars) + 1)]
    dump_pct   = ((cur_close - dump_start) / dump_start * 100.0) if dump_start > 0 else 0.0

    # Volume spike: current bar volume vs recent average
    vol_avg    = sum(volumes[-(int(min_dump_bars) + 2):-1]) / max(int(min_dump_bars), 1)
    vol_spike  = (volumes[-1] / vol_avg) if vol_avg > 1e-10 else 1.0

    # Session range context
    session_high = max(highs[-int(min_dump_bars):])
    session_low  = min(lows[-int(min_dump_bars):])
    near_low_pct = ((cur_close - session_low) / session_low * 100.0) if session_low > 0 else 999.0

    ctx = market_context(ohlcv=ohlcv, window=int(filter_window or max(sma_len, rsi_len, 8)))

    ind = {
        "rsi":          round(cur_rsi, 1),
        "sma":          round(cur_ma, 6),
        "close":        round(cur_close, 6),
        "dump_pct":     round(dump_pct, 2),
        "vol_spike":    round(vol_spike, 2),
        "near_low_pct": round(near_low_pct, 2),
        "session_high": round(session_high, 6),
        "session_low":  round(session_low, 6),
        "avg_range_pct":ctx["avg_range_pct"],
        "volume_ratio": ctx["volume_ratio"],
        "trend_efficiency": ctx["trend_efficiency"],
    }

    # EXIT: RSI recovered
    if cur_rsi >= float(rsi_exit):
        return {"ok": True, "action": "sell", "reason": "rsi_recovered_exit", "ind": ind}

    # ENTRY filters
    dumped    = dump_pct <= -abs(float(min_dump_pct))
    oversold  = cur_rsi < float(rsi_oversold)
    near_bot  = near_low_pct <= 3.0
    vol_ok    = (vol_spike >= 1.3) if bool(require_volume_spike) else True

    if dumped and oversold and near_bot and vol_ok:
        if max_volatility_pct is not None and ctx["avg_range_pct"] > float(max_volatility_pct):
            return {"ok": True, "action": "hold", "reason": "volatility_too_high", "ind": ind}
        if min_volume_ratio is not None and ctx["volume_ratio"] < float(min_volume_ratio):
            return {"ok": True, "action": "hold", "reason": "low_volume_filter", "ind": ind}
        return {"ok": True, "action": "buy", "reason": "volatility_reversal_entry", "ind": ind}

    reasons = []
    if not dumped:   reasons.append(f"dump_pct={dump_pct:.1f}%>={-min_dump_pct}%")
    if not oversold: reasons.append(f"rsi={cur_rsi:.0f}>={rsi_oversold}")
    if not near_bot: reasons.append(f"near_low={near_low_pct:.1f}%>3%")
    if not vol_ok:   reasons.append(f"vol_spike={vol_spike:.1f}<1.3")

    return {"ok": True, "action": "hold", "reason": "filters_failed:" + ",".join(reasons), "ind": ind}
