from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class MarketRules:
    venue: str
    canonical_symbol: str   # BTC-USDT
    native_symbol: str      # Binance: BTCUSDT, Gate: BTC_USDT, Coinbase: BTC-USD
    active: bool
    min_notional: Optional[float] = None
    min_qty: Optional[float] = None
    qty_step: Optional[float] = None
    price_tick: Optional[float] = None
    meta: Dict[str, Any] = None

@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    code: str
    message: str
    rules: Optional[MarketRules] = None
    meta: Dict[str, Any] = None
