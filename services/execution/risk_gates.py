from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from services.risk.live_risk_gates_phase82 import LiveGateDB, LiveRiskGates, LiveRiskLimits  # canonical


@dataclass(frozen=True)
class GateDecision:
    ok: bool
    reason: str
    details: Dict[str, Any]


def evaluate_live_intent(
    *,
    intent: Dict[str, Any],
    realized_pnl_usd: float = 0.0,
    exec_db_path: str,
    limits: LiveRiskLimits | None = None,
) -> GateDecision:
    cfg_limits = limits or LiveRiskLimits.from_trading_yaml()
    if cfg_limits is None:
        return GateDecision(ok=True, reason="limits_unconfigured", details={})

    gate = LiveRiskGates(limits=cfg_limits, db=LiveGateDB(exec_db=exec_db_path))
    allowed, reason, details = gate.check_live(it=dict(intent or {}), realized_pnl_usd=float(realized_pnl_usd))
    return GateDecision(ok=bool(allowed), reason=str(reason), details=dict(details or {}))

from services.security.binance_guard import require_binance_allowed
