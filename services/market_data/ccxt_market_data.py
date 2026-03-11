from __future__ import annotations

from dataclasses import dataclass

from services.backtest.signal_replay import fetch_ohlcv


@dataclass(frozen=True)
class MarketDataCfg:
    exchange_id: str
    default_type: str = "spot"
    sandbox: bool = False


class CCXTMarketData:
    def __init__(self, cfg: MarketDataCfg):
        self.cfg = cfg

    def ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> list[list]:
        return fetch_ohlcv(self.cfg.exchange_id, symbol, timeframe=timeframe, limit=int(limit))
