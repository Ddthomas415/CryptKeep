from __future__ import annotations
"""
DEPRECATED — this module is in a transitional service family scheduled for
removal on 2026-07-01. See docs/ARCHITECTURE.md for the migration plan.
Import from the canonical path instead.
"""
import warnings as _warnings
_warnings.warn(
    f"{{__name__}} is deprecated and will be removed 2026-07-01. "
    "Use 'services/strategies/strategy_registry.py' instead. See docs/ARCHITECTURE.md.",
    DeprecationWarning,
    stacklevel=2,
)


from typing import Callable, Dict, Any

from services.strategy.signals import Signal
from services.strategy.strategies.ema_crossover import compute as ema_crossover
from services.strategy.strategies.mean_reversion import compute as mean_reversion
from services.strategy.strategies.breakout import compute as breakout

STRATEGIES: dict[str, Callable[[list[list[float]]], Signal]] = {
    "ema_crossover": ema_crossover,
    "mean_reversion": mean_reversion,
    "breakout": breakout,
}

DEFAULT_PARAMS: dict[str, dict[str, Any]] = {
    "ema_crossover": {"fast": 12, "slow": 26},
    "mean_reversion": {"lookback": 50, "entry_z": 2.0},
    "breakout": {"lookback": 20},
}

def get_strategy(name: str):
    n = str(name)
    if n not in STRATEGIES:
        raise ValueError(f"unknown_strategy:{n}")
    return STRATEGIES[n]

def get_default_params(name: str) -> dict[str, Any]:
    return dict(DEFAULT_PARAMS.get(str(name), {}))
