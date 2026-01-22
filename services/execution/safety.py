from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from services.config_loader import load_user_config
from storage.execution_guard_store_sqlite import ExecutionGuardStoreSQLite

def _today() -> str:
    return date.today().isoformat()

@dataclass(frozen=True)
class SafetyGates:
    min_order_notional: float = 0.0
    max_trades_per_day: int = 0
    max_daily_loss: float = 0.0
    # canonical realized pnl comes from data/pnl.sqliten
    prefer_journal_pnl: bool = False
def load_gates() -> SafetyGates:
    cfg = load_user_config()
    s = cfg.get("safety") if isinstance(cfg.get("safety"), dict) else {}
    return SafetyGates(
        min_order_notional=float(s.get("min_order_notional", 0.0) or 0.0),
        max_trades_per_day=int(s.get("max_trades_per_day", 0) or 0),
        max_daily_loss=float(s.get("max_daily_loss", 0.0) or 0.0),
        prefer_journal_pnl=bool(s.get("prefer_journal_pnl", False)),    )

def current_day_state(store: ExecutionGuardStoreSQLite) -> Dict[str, Any]:
    m = store.get_today_metrics()
    gates = load_gates()
    return m

def should_allow_order(
    venue: str,
    symbol: str,
    side: str,
    qty: float,
    price: float,
    gates: SafetyGates,
    store: ExecutionGuardStoreSQLite,
) -> Tuple[bool, str]:
    notional = float(qty) * float(price)
    if gates.min_order_notional and notional < float(gates.min_order_notional):
        return False, "min_order_notional"
    m = store.get_today_metrics()
    trades = int(m.get("trades", 0))
    if gates.max_trades_per_day and trades >= int(gates.max_trades_per_day):
        return False, "max_trades_per_day"
    if gates.max_daily_loss and float(gates.max_daily_loss) > 0:
        pnl = float(m.get("approx_realized_pnl", 0.0))
        if pnl <= -float(gates.max_daily_loss):
            return False, "max_daily_loss"
    return True, "ok"
