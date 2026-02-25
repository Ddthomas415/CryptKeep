from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class RiskGateState(str, Enum):
    ALLOW_TRADING = "ALLOW_TRADING"
    ALLOW_ONLY_REDUCTIONS = "ALLOW_ONLY_REDUCTIONS"
    HALT_NEW_POSITIONS = "HALT_NEW_POSITIONS"
    FULL_STOP = "FULL_STOP"


@dataclass(frozen=True)
class RawSignalSnapshot:
    ts: str
    source: str
    exchange_api_ok: bool
    order_reject_rate: float
    ws_lag_ms: float
    venue_latency_ms: float
    realized_volatility: float
    drawdown_pct: float
    pnl_usd: float
    exposure_usd: float
    leverage: float
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> "RawSignalSnapshot":
        p = dict(payload or {})
        return RawSignalSnapshot(
            ts=str(p.get("ts") or ""),
            source=str(p.get("source") or "bot"),
            exchange_api_ok=bool(p.get("exchange_api_ok", False)),
            order_reject_rate=float(p.get("order_reject_rate", 0.0) or 0.0),
            ws_lag_ms=float(p.get("ws_lag_ms", 0.0) or 0.0),
            venue_latency_ms=float(p.get("venue_latency_ms", 0.0) or 0.0),
            realized_volatility=float(p.get("realized_volatility", 0.0) or 0.0),
            drawdown_pct=float(p.get("drawdown_pct", 0.0) or 0.0),
            pnl_usd=float(p.get("pnl_usd", 0.0) or 0.0),
            exposure_usd=float(p.get("exposure_usd", 0.0) or 0.0),
            leverage=float(p.get("leverage", 0.0) or 0.0),
            extra=dict(p.get("extra") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts": self.ts,
            "source": self.source,
            "exchange_api_ok": self.exchange_api_ok,
            "order_reject_rate": self.order_reject_rate,
            "ws_lag_ms": self.ws_lag_ms,
            "venue_latency_ms": self.venue_latency_ms,
            "realized_volatility": self.realized_volatility,
            "drawdown_pct": self.drawdown_pct,
            "pnl_usd": self.pnl_usd,
            "exposure_usd": self.exposure_usd,
            "leverage": self.leverage,
            "extra": dict(self.extra),
        }


@dataclass(frozen=True)
class RiskGateSignal:
    ts: str
    source: str
    system_stress: float
    regime: str
    zone: str
    gate_state: RiskGateState
    hazards: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> "RiskGateSignal":
        p = dict(payload or {})
        return RiskGateSignal(
            ts=str(p.get("ts") or ""),
            source=str(p.get("source") or "ops_intel"),
            system_stress=float(p.get("system_stress", 0.0) or 0.0),
            regime=str(p.get("regime") or "unknown"),
            zone=str(p.get("zone") or "unknown"),
            gate_state=RiskGateState(str(p.get("gate_state") or RiskGateState.ALLOW_TRADING.value)),
            hazards=[str(v) for v in (p.get("hazards") or [])],
            reasons=[str(v) for v in (p.get("reasons") or [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts": self.ts,
            "source": self.source,
            "system_stress": self.system_stress,
            "regime": self.regime,
            "zone": self.zone,
            "gate_state": self.gate_state.value,
            "hazards": list(self.hazards),
            "reasons": list(self.reasons),
        }


def evaluate_gate_for_order(gate_state: RiskGateState | str, *, reduce_only: bool) -> tuple[bool, str]:
    state = gate_state if isinstance(gate_state, RiskGateState) else RiskGateState(str(gate_state))

    if state == RiskGateState.FULL_STOP:
        return False, "full_stop"
    if state in (RiskGateState.ALLOW_ONLY_REDUCTIONS, RiskGateState.HALT_NEW_POSITIONS) and not bool(
        reduce_only
    ):
        return False, "reductions_only"
    return True, "ok"

