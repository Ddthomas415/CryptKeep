from __future__ import annotations

from typing import Any
from services.strategies.base import Strategy, MarketContext, PositionContext, Signal, OrderIntent
from services.strategies.ema_cross import ema_crossover_signal

class EmaCrossStrategy:
    name = "ema_cross"

    def compute_signal(self, *, cfg: dict, market: MarketContext, position: PositionContext) -> Signal:
        strat = cfg.get("strategy") if isinstance(cfg.get("strategy"), dict) else {}
        fast = int(strat.get("ema_fast", 12))
        slow = int(strat.get("ema_slow", 26))

        closes = [float(x[4]) for x in (market.ohlcv or []) if isinstance(x, (list, tuple)) and len(x) >= 5]
        r = ema_crossover_signal(closes=closes, fast=fast, slow=slow)
        if not bool(r.get("ok")):
            return Signal(name=self.name, action="hold", confidence=0.0, detail={"reason": r.get("reason")})

        act = str(r.get("signal") or "hold")
        return Signal(
            name=self.name,
            action=act,
            confidence=0.6 if act in ("buy","sell") else 0.4,
            detail={"fast_ema": r.get("fast_ema"), "slow_ema": r.get("slow_ema"), "cross_up": r.get("cross_up"), "cross_down": r.get("cross_down")},
        )

    def suggest_orders(self, *, cfg: dict, market: MarketContext, position: PositionContext, signal: Signal) -> list[OrderIntent]:
        # Strategy only proposes direction; sizing is handled outside (risk engine) for buys.
        if signal.action == "buy" and position.base_amt <= 0:
            return [OrderIntent(side="buy", reason="ema_cross_buy")]
        if signal.action == "sell" and position.base_amt > 0:
            return [OrderIntent(side="sell", reason="ema_cross_sell")]
        return []
