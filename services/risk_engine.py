from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional
from core.models import Intent, PortfolioState, RiskDecision
import os

def utc_day_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

@dataclass
class RiskConfig:
    max_abs_qty: float = 0.01
    max_trades_per_day: int = 50
    kill_switch_env: str = "CBP_KILL"

class RiskEngine:
    def __init__(self, cfg: RiskConfig) -> None:
        self.cfg = cfg
        self._day = utc_day_key()
        self._trade_count: Dict[str, int] = {}

    def _count_today(self) -> int:
        day = utc_day_key()
        if day != self._day:
            self._day = day
        return self._trade_count.get(self._day, 0)

    def _inc_today(self) -> None:
        day = utc_day_key()
        if day != self._day:
            self._day = day
        self._trade_count[self._day] = self._trade_count.get(self._day, 0) + 1

    def allow_intent(self, intent: Intent, ps: PortfolioState, current_price: Optional[float]) -> RiskDecision:
        if os.environ.get(self.cfg.kill_switch_env, "").strip().lower() in ("1", "true", "yes", "on"):
            return RiskDecision(allowed=False, reason="kill_switch_enabled")
        if abs(intent.target_qty) > self.cfg.max_abs_qty:
            return RiskDecision(allowed=False, reason="max_abs_qty_exceeded", max_qty=self.cfg.max_abs_qty)
        if self._count_today() >= self.cfg.max_trades_per_day:
            return RiskDecision(allowed=False, reason="max_trades_per_day_exceeded")
        return RiskDecision(allowed=True)

    def record_trade(self) -> None:
        self._inc_today()
