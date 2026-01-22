from __future__ import annotations

import math
from services.strategies.base import Strategy, MarketContext, PositionContext, Signal, OrderIntent

def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 2:
        return None
    gains = 0.0
    losses = 0.0
    for a, b in zip(closes[-(period+1):-1], closes[-period:]):
        d = float(b) - float(a)
        if d > 0:
            gains += d
        else:
            losses += -d
    if gains + losses == 0:
        return 50.0
    rs = gains / max(losses, 1e-12)
    return 100.0 - (100.0 / (1.0 + rs))

class MeanReversionRsiStrategy:
    name = "mean_reversion_rsi"

    def compute_signal(self, *, cfg: dict, market: MarketContext, position: PositionContext) -> Signal:
        strat = cfg.get("strategy") if isinstance(cfg.get("strategy"), dict) else {}
        enabled = bool(strat.get("mr_enabled", False))  # default False = safe hold
        period = int(strat.get("mr_rsi_period", 14))
        buy_below = float(strat.get("mr_buy_below", 30.0))
        sell_above = float(strat.get("mr_sell_above", 70.0))

        closes = [float(x[4]) for x in (market.ohlcv or []) if isinstance(x, (list, tuple)) and len(x) >= 5]
        r = _rsi(closes, period=period)
        if r is None:
            return Signal(name=self.name, action="hold", confidence=0.0, detail={"reason":"not_enough_data"})

        if not enabled:
            return Signal(name=self.name, action="hold", confidence=0.2, detail={"rsi": r, "note":"mr_disabled_by_default"})

        if r <= buy_below:
            return Signal(name=self.name, action="buy", confidence=0.55, detail={"rsi": r})
        if r >= sell_above:
            return Signal(name=self.name, action="sell", confidence=0.55, detail={"rsi": r})
        return Signal(name=self.name, action="hold", confidence=0.35, detail={"rsi": r})

    def suggest_orders(self, *, cfg: dict, market: MarketContext, position: PositionContext, signal: Signal) -> list[OrderIntent]:
        if signal.action == "buy" and position.base_amt <= 0:
            return [OrderIntent(side="buy", reason="mr_rsi_buy")]
        if signal.action == "sell" and position.base_amt > 0:
            return [OrderIntent(side="sell", reason="mr_rsi_sell")]
        return []
