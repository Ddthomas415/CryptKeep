from __future__ import annotations
from services.strategies.live_base import LiveStrategy, LiveContext, LiveDecision

def _ema(series, span: int):
    return series.ewm(span=int(span), adjust=False).mean()

def _cross_up(f_prev, s_prev, f, s) -> bool:
    return (f_prev <= s_prev) and (f > s)

def _cross_dn(f_prev, s_prev, f, s) -> bool:
    return (f_prev >= s_prev) and (f < s)

class EMACrossoverLive(LiveStrategy):
    name = "ema_crossover"

    def __init__(self, *, fast: int = 12, slow: int = 26):
        self.fast = int(fast)
        self.slow = int(slow)

    def decide(self, df, ctx: LiveContext) -> LiveDecision:
        if df is None or len(df) < max(self.fast, self.slow) + 3:
            return LiveDecision(action="hold", reason="insufficient_candles")

        close = df["close"].astype(float)
        fast = _ema(close, self.fast)
        slow = _ema(close, self.slow)

        f_prev, s_prev = float(fast.iloc[-2]), float(slow.iloc[-2])
        f, s = float(fast.iloc[-1]), float(slow.iloc[-1])

        is_open = float(ctx.position_qty) > 0.0

        if (not is_open) and _cross_up(f_prev, s_prev, f, s):
            return LiveDecision(action="enter", side="buy", reason="ema_cross_up")

        if is_open and _cross_dn(f_prev, s_prev, f, s):
            return LiveDecision(action="exit", side="sell", reason="ema_cross_down")

        return LiveDecision(action="hold", reason="no_signal")
