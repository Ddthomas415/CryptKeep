from __future__ import annotations

from services.strategies.ema_cross import signal_from_ohlcv as ema_cross
from services.strategies.mean_reversion_rsi import signal_from_ohlcv as mean_rev_rsi
from services.strategies.breakout_donchian import signal_from_ohlcv as breakout_donchian
from services.strategies.momentum import compute_signal as momentum_compute_signal
from services.strategies.volatility_reversal import signal_from_ohlcv as volatility_reversal
from services.strategies.gap_fill import signal_from_ohlcv as gap_fill
from services.strategies.breakout_volume import signal_from_ohlcv as breakout_volume

SUPPORTED = {
    "ema_cross": ema_cross,
    "mean_reversion_rsi": mean_rev_rsi,
    "breakout_donchian": breakout_donchian,
    "momentum": momentum_compute_signal,
    "volatility_reversal": volatility_reversal,
    "gap_fill": gap_fill,
    "breakout_volume": breakout_volume,
}

def compute_signal(*, cfg: dict, symbol: str, ohlcv: list) -> dict:
    st = cfg.get("strategy") if isinstance(cfg.get("strategy"), dict) else {}
    name = str(st.get("name", "ema_cross")).strip()
    if name not in SUPPORTED:
        name = "ema_cross"

    if not bool(st.get("trade_enabled", True)):
        return {"ok": True, "action": "hold", "reason": "trade_disabled", "strategy": name, "symbol": symbol}

    fn = SUPPORTED[name]

    if name == "ema_cross":
        return {
            **fn(
                ohlcv=ohlcv,
                ema_fast=int(st.get("ema_fast", 12)),
                ema_slow=int(st.get("ema_slow", 26)),
                filter_window=int(st["filter_window"]) if "filter_window" in st else None,
                min_volatility_pct=float(st["min_volatility_pct"]) if "min_volatility_pct" in st else None,
                min_volume_ratio=float(st["min_volume_ratio"]) if "min_volume_ratio" in st else None,
                min_trend_efficiency=float(st["min_trend_efficiency"]) if "min_trend_efficiency" in st else None,
                min_cross_gap_pct=float(st["min_cross_gap_pct"]) if "min_cross_gap_pct" in st else None,
            ),
            "strategy": name,
            "symbol": symbol,
        }

    if name == "mean_reversion_rsi":
        return {
            **fn(
                ohlcv=ohlcv,
                rsi_len=int(st.get("rsi_len", 14)),
                rsi_buy=float(st.get("rsi_buy", 30.0)),
                rsi_sell=float(st.get("rsi_sell", 70.0)),
                sma_len=int(st.get("sma_len", 50)),
                filter_window=int(st["filter_window"]) if "filter_window" in st else None,
                max_volatility_pct=float(st["max_volatility_pct"]) if "max_volatility_pct" in st else None,
                min_volume_ratio=float(st["min_volume_ratio"]) if "min_volume_ratio" in st else None,
                max_trend_efficiency=float(st["max_trend_efficiency"]) if "max_trend_efficiency" in st else None,
                max_sma_distance_pct=float(st["max_sma_distance_pct"]) if "max_sma_distance_pct" in st else None,
                require_reversal_confirmation=bool(st.get("require_reversal_confirmation", False)),
            ),
            "strategy": name,
            "symbol": symbol,
        }

    if name == "breakout_donchian":
        return {
            **fn(
                ohlcv=ohlcv,
                donchian_len=int(st.get("donchian_len", 20)),
                filter_window=int(st["filter_window"]) if "filter_window" in st else None,
                min_volatility_pct=float(st["min_volatility_pct"]) if "min_volatility_pct" in st else None,
                min_volume_ratio=float(st["min_volume_ratio"]) if "min_volume_ratio" in st else None,
                min_trend_efficiency=float(st["min_trend_efficiency"]) if "min_trend_efficiency" in st else None,
                min_channel_width_pct=float(st["min_channel_width_pct"]) if "min_channel_width_pct" in st else None,
                breakout_buffer_pct=float(st["breakout_buffer_pct"]) if "breakout_buffer_pct" in st else None,
                require_directional_confirmation=bool(st.get("require_directional_confirmation", False)),
            ),
            "strategy": name,
            "symbol": symbol,
        }

    if name == "momentum":
        return {
            **fn(
                cfg=cfg,
                symbol=symbol,
                ohlcv=ohlcv,
            ),
            "strategy": name,
            "symbol": symbol,
        }

    if name == "volatility_reversal":
        return {
            **fn(
                ohlcv=ohlcv,
                rsi_len=int(st.get("rsi_len", 14)),
                rsi_oversold=float(st.get("rsi_oversold", 28.0)),
                rsi_exit=float(st.get("rsi_exit", 50.0)),
                sma_len=int(st.get("sma_len", 20)),
                filter_window=int(st["filter_window"]) if "filter_window" in st else None,
                min_dump_bars=int(st.get("min_dump_bars", 3)),
                min_dump_pct=float(st.get("min_dump_pct", 8.0)),
                max_volatility_pct=float(st["max_volatility_pct"]) if "max_volatility_pct" in st else None,
                min_volume_ratio=float(st["min_volume_ratio"]) if "min_volume_ratio" in st else None,
                require_volume_spike=bool(st.get("require_volume_spike", True)),
            ),
            "strategy": name,
            "symbol": symbol,
        }

    if name == "gap_fill":
        return {
            **fn(
                ohlcv=ohlcv,
                rsi_len=int(st.get("rsi_len", 14)),
                rsi_buy=float(st.get("rsi_buy", 40.0)),
                rsi_sell=float(st.get("rsi_sell", 60.0)),
                sma_len=int(st.get("sma_len", 20)),
                filter_window=int(st["filter_window"]) if "filter_window" in st else None,
                min_gap_pct=float(st.get("min_gap_pct", 3.0)),
                gap_fill_target_pct=float(st.get("gap_fill_target_pct", 0.618)),
                min_volume_ratio=float(st["min_volume_ratio"]) if "min_volume_ratio" in st else None,
            ),
            "strategy": name,
            "symbol": symbol,
        }

    if name == "breakout_volume":
        return {
            **fn(
                ohlcv=ohlcv,
                donchian_len=int(st.get("donchian_len", 20)),
                sma_len=int(st.get("sma_len", 50)),
                filter_window=int(st["filter_window"]) if "filter_window" in st else None,
                min_volume_ratio=float(st.get("min_volume_ratio", 2.0)),
                min_volatility_pct=float(st["min_volatility_pct"]) if "min_volatility_pct" in st else None,
                min_trend_efficiency=float(st["min_trend_efficiency"]) if "min_trend_efficiency" in st else None,
                breakout_buffer_pct=float(st.get("breakout_buffer_pct", 0.1)),
                min_channel_width_pct=float(st.get("min_channel_width_pct", 1.0)),
                require_close_above=bool(st.get("require_close_above", True)),
            ),
            "strategy": name,
            "symbol": symbol,
        }

    return {"ok": True, "action": "hold", "reason": "unknown_strategy", "strategy": name, "symbol": symbol}
