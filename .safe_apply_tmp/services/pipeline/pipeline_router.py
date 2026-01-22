from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from services.pipeline.ema_strategy import EMACrossoverPipeline, EMAStrategyCfg
from services.pipeline.mean_reversion_strategy import MeanReversionBBPipeline, MeanReversionCfg

@dataclass
class RouterCfg:
    exec_db: str
    exchange_id: str
    symbol: str
    timeframe: str
    ohlcv_limit: int
    mode: str
    fixed_qty: float
    quote_notional: float
    only_on_new_bar: bool

    # strategy selector
    strategy: str = "ema"  # ema | mean_reversion

    # ema params
    ema_fast: int = 12
    ema_slow: int = 26

    # mean reversion params
    bb_window: int = 20
    bb_k: float = 2.0

def build_pipeline(cfg: RouterCfg):
    s = (cfg.strategy or "ema").strip().lower()
    if s == "mean_reversion":
        return MeanReversionBBPipeline(MeanReversionCfg(
            exec_db=cfg.exec_db,
            exchange_id=cfg.exchange_id,
            symbol=cfg.symbol,
            timeframe=cfg.timeframe,
            ohlcv_limit=cfg.ohlcv_limit,
            bb_window=int(cfg.bb_window),
            bb_k=float(cfg.bb_k),
            mode=cfg.mode,
            fixed_qty=float(cfg.fixed_qty),
            quote_notional=float(cfg.quote_notional),
            only_on_new_bar=bool(cfg.only_on_new_bar),
        ))
    # default ema
    return EMACrossoverPipeline(EMAStrategyCfg(
        exec_db=cfg.exec_db,
        exchange_id=cfg.exchange_id,
        symbol=cfg.symbol,
        timeframe=cfg.timeframe,
        fast=int(cfg.ema_fast),
        slow=int(cfg.ema_slow),
        ohlcv_limit=cfg.ohlcv_limit,
        mode=cfg.mode,
        fixed_qty=float(cfg.fixed_qty),
        quote_notional=float(cfg.quote_notional),
        only_on_new_bar=bool(cfg.only_on_new_bar),
    ))
