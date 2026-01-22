from __future__ import annotations

from services.strategies.ema_cross import signal_from_ohlcv as ema_cross
from services.strategies.mean_reversion_rsi import signal_from_ohlcv as mean_rev_rsi
from services.strategies.breakout_donchian import signal_from_ohlcv as breakout_donchian

SUPPORTED = {
    "ema_cross": ema_cross,
    "mean_reversion_rsi": mean_rev_rsi,
    "breakout_donchian": breakout_donchian,
}

def compute_signal(*, cfg: dict, symbol: str, ohlcv: list) -> dict:
    st = cfg.get("strategy") if isinstance(cfg.get("strategy"), dict) else {}
    name = str(st.get("name", "ema_cross")).strip()
    if name not in SUPPORTED:
        name = "ema_cross"

    if not bool(st.get("trade_enabled", True)):
        return {"ok": True, "action": "hold", "reason": "trade_disabled", "strategy": name}

    fn = SUPPORTED[name]

    if name == "ema_cross":
        return {**fn(ohlcv=ohlcv, ema_fast=int(st.get("ema_fast", 12)), ema_slow=int(st.get("ema_slow", 26))), "strategy": name, "symbol": symbol}
    if name == "mean_reversion_rsi":
        return {**fn(
            ohlcv=ohlcv,
            rsi_len=int(st.get("rsi_len", 14)),
            rsi_buy=float(st.get("rsi_buy", 30.0)),
            rsi_sell=float(st.get("rsi_sell", 70.0)),
            sma_len=int(st.get("sma_len", 50)),
        ), "strategy": name, "symbol": symbol}
    if name == "breakout_donchian":
        return {**fn(ohlcv=ohlcv, donchian_len=int(st.get("donchian_len", 20))), "strategy": name, "symbol": symbol}

    return {"ok": True, "action": "hold", "reason": "unknown_strategy", "strategy": name, "symbol": symbol}
