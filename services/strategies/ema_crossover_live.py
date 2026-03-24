from __future__ import annotations
from services.strategies.live_base import LiveStrategy, LiveContext, LiveDecision
from services.strategies.ema_cross import ema_crossover_signal

class EMACrossoverLive(LiveStrategy):
    name = "ema_crossover"

    def __init__(self, *, fast: int = 12, slow: int = 26):
        self.fast = int(fast)
        self.slow = int(slow)

    def decide(self, df, ctx: LiveContext) -> LiveDecision:
        closes = []
        if df is not None and "close" in df:
            closes = [float(x) for x in df["close"].astype(float).tolist()]

        r = ema_crossover_signal(closes=closes, fast=self.fast, slow=self.slow)
        if not bool(r.get("ok")):
            return LiveDecision(action="hold", reason=str(r.get("reason") or "insufficient_candles"))

        is_open = float(ctx.position_qty) > 0.0
        sig = str(r.get("signal") or "hold")

        if (not is_open) and sig == "buy":
            return LiveDecision(action="enter", side="buy", reason="ema_cross_up")

        if is_open and sig == "sell":
            return LiveDecision(action="exit", side="sell", reason="ema_cross_down")

        return LiveDecision(action="hold", reason="no_signal")
