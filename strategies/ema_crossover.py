from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


def ema(prev: Optional[float], x: float, alpha: float) -> float:
    if prev is None:
        return x
    return alpha * x + (1 - alpha) * prev


@dataclass
class EMACfg:
    fast: int = 12
    slow: int = 26
    min_history: int = 30
    trade_qty: float = 0.01


@dataclass
class EMAState:
    # per symbol state
    ema_fast: Optional[float] = None
    ema_slow: Optional[float] = None
    last_signal: int = 0  # -1 sell, 0 neutral, +1 buy


def update_ema_state(px: float, cfg: EMACfg, st: EMAState) -> EMAState:
    a_fast = 2.0 / (cfg.fast + 1.0)
    a_slow = 2.0 / (cfg.slow + 1.0)
    st.ema_fast = ema(st.ema_fast, px, a_fast)
    st.ema_slow = ema(st.ema_slow, px, a_slow)
    return st


def compute_signal(st: EMAState) -> int:
    if st.ema_fast is None or st.ema_slow is None:
        return 0
    if st.ema_fast > st.ema_slow:
        return +1
    if st.ema_fast < st.ema_slow:
        return -1
    return 0
