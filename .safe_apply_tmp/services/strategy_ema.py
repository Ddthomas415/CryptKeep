from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from core.models import Intent

@dataclass
class EMAState:
    alpha: float
    value: Optional[float] = None

    def update(self, x: float) -> float:
        if self.value is None:
            self.value = x
        else:
            self.value = self.alpha * x + (1.0 - self.alpha) * self.value
        return self.value

def ema_alpha(period: int) -> float:
    if period <= 0:
        raise ValueError("EMA period must be > 0")
    return 2.0 / (period + 1.0)

@dataclass
class EMACrossStrategy:
    venue: str
    symbol: str
    target_qty: float
    fast_period: int = 5   # faster for quicker signals
    slow_period: int = 10
    max_slippage_bps: float = 10.0
    _fast: EMAState = None
    _slow: EMAState = None
    _last_signal: Optional[str] = None

    def __post_init__(self) -> None:
        self._fast = EMAState(alpha=ema_alpha(self.fast_period))
        self._slow = EMAState(alpha=ema_alpha(self.slow_period))

    def on_price(self, price: float) -> Optional[Intent]:
        f = self._fast.update(price)
        s = self._slow.update(price)
        if self._fast.value is None or self._slow.value is None:
            return None
        signal = "long" if f > s else "short" if f < s else None
        if signal is None or signal == self._last_signal:
            return None
        self._last_signal = signal
        tq = abs(self.target_qty)
        target = tq if signal == "long" else -tq
        return Intent(
            strategy="ema_cross",
            venue=self.venue,
            symbol=self.symbol,
            target_qty=target,
            max_slippage_bps=self.max_slippage_bps,
            urgency=0.5,
        )
