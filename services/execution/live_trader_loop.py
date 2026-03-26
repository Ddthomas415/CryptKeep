from __future__ import annotations

from services.strategy_runner.ema_crossover_runner import run_forever as run_strategy_runner_forever

def run_forever_live() -> None:
    run_strategy_runner_forever()
