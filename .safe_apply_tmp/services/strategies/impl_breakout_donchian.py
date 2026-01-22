from __future__ import annotations

from services.strategies.base import Strategy, MarketContext, PositionContext, Signal, OrderIntent

class BreakoutDonchianStrategy:
    name = "breakout_donchian"

    def compute_signal(self, *, cfg: dict, market: MarketContext, position: PositionContext) -> Signal:
        strat = cfg.get("strategy") if isinstance(cfg.get("strategy"), dict) else {}
        enabled = bool(strat.get("bo_enabled", False))  # default False
        lookback = int(strat.get("bo_lookback", 20))

        ohlcv = market.ohlcv or []
        if len(ohlcv) < lookback + 3:
            return Signal(name=self.name, action="hold", confidence=0.0, detail={"reason":"not_enough_data"})

        highs = [float(x[2]) for x in ohlcv[-lookback:] if isinstance(x, (list, tuple)) and len(x) >= 3]
        lows  = [float(x[3]) for x in ohlcv[-lookback:] if isinstance(x, (list, tuple)) and len(x) >= 4]
        if not highs or not lows:
            return Signal(name=self.name, action="hold", confidence=0.0, detail={"reason":"bad_ohlcv"})

        top = max(highs)
        bot = min(lows)
        px = float(market.last_price)

        if not enabled:
            return Signal(name=self.name, action="hold", confidence=0.2, detail={"top": top, "bot": bot, "note":"bo_disabled_by_default"})

        if px > top:
            return Signal(name=self.name, action="buy", confidence=0.55, detail={"top": top, "bot": bot})
        if px < bot:
            return Signal(name=self.name, action="sell", confidence=0.55, detail={"top": top, "bot": bot})
        return Signal(name=self.name, action="hold", confidence=0.35, detail={"top": top, "bot": bot})

    def suggest_orders(self, *, cfg: dict, market: MarketContext, position: PositionContext, signal: Signal) -> list[OrderIntent]:
        if signal.action == "buy" and position.base_amt <= 0:
            return [OrderIntent(side="buy", reason="donchian_breakout_buy")]
        if signal.action == "sell" and position.base_amt > 0:
            return [OrderIntent(side="sell", reason="donchian_breakout_sell")]
        return []
