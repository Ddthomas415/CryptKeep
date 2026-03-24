from __future__ import annotations

from services.strategy_runner.strategies.ema_crossover import (
    EMACfg,
    EMAState,
    update_ema_state,
    compute_signal,
)


class EMACrossStrategy:
    def __init__(self, fast: int, slow: int, min_history: int | None = None):
        self.cfg = EMACfg(
            fast=int(fast),
            slow=int(slow),
            min_history=int(min_history or (max(int(fast), int(slow)) + 2)),
        )
        self.state = EMAState()

    def on_price(self, price: float):
        self.state = update_ema_state(float(price), self.cfg, self.state)
        return compute_signal(self.state)
