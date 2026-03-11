from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from services.ops.risk_gate_contract import RawSignalSnapshot, RiskGateSignal, RiskGateState
from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clip01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _as_snapshot(payload: RawSignalSnapshot | Dict[str, Any]) -> RawSignalSnapshot:
    return payload if isinstance(payload, RawSignalSnapshot) else RawSignalSnapshot.from_dict(payload)


@dataclass(frozen=True)
class RiskGateThresholds:
    # Connectivity / execution health
    reject_rate_warn: float = 0.05
    reject_rate_block: float = 0.15
    ws_lag_warn_ms: float = 1200.0
    ws_lag_block_ms: float = 2500.0
    venue_latency_warn_ms: float = 800.0
    venue_latency_block_ms: float = 2000.0

    # Portfolio / risk stress
    drawdown_warn_pct: float = 5.0
    drawdown_block_pct: float = 12.0
    leverage_warn: float = 2.0
    leverage_block: float = 4.0
    realized_vol_warn: float = 0.03
    realized_vol_block: float = 0.08


def _hazards(snapshot: RawSignalSnapshot, th: RiskGateThresholds) -> list[str]:
    hz: list[str] = []
    if not bool(snapshot.exchange_api_ok):
        hz.append("exchange_api_down")
    if float(snapshot.order_reject_rate) >= float(th.reject_rate_block):
        hz.append("reject_rate_block")
    elif float(snapshot.order_reject_rate) >= float(th.reject_rate_warn):
        hz.append("reject_rate_warn")

    if float(snapshot.ws_lag_ms) >= float(th.ws_lag_block_ms):
        hz.append("ws_lag_block")
    elif float(snapshot.ws_lag_ms) >= float(th.ws_lag_warn_ms):
        hz.append("ws_lag_warn")

    if float(snapshot.venue_latency_ms) >= float(th.venue_latency_block_ms):
        hz.append("venue_latency_block")
    elif float(snapshot.venue_latency_ms) >= float(th.venue_latency_warn_ms):
        hz.append("venue_latency_warn")

    if float(snapshot.drawdown_pct) >= float(th.drawdown_block_pct):
        hz.append("drawdown_block")
    elif float(snapshot.drawdown_pct) >= float(th.drawdown_warn_pct):
        hz.append("drawdown_warn")

    if float(snapshot.leverage) >= float(th.leverage_block):
        hz.append("leverage_block")
    elif float(snapshot.leverage) >= float(th.leverage_warn):
        hz.append("leverage_warn")

    if float(snapshot.realized_volatility) >= float(th.realized_vol_block):
        hz.append("volatility_block")
    elif float(snapshot.realized_volatility) >= float(th.realized_vol_warn):
        hz.append("volatility_warn")
    return hz


def classify_regime(snapshot: RawSignalSnapshot | Dict[str, Any], th: RiskGateThresholds | None = None) -> str:
    snap = _as_snapshot(snapshot)
    t = th or RiskGateThresholds()
    rv = float(snap.realized_volatility)
    if rv >= float(t.realized_vol_block):
        return "extreme"
    if rv >= float(t.realized_vol_warn):
        return "high"
    if rv <= float(t.realized_vol_warn) / 3.0:
        return "low"
    return "normal"


def compute_system_stress(snapshot: RawSignalSnapshot | Dict[str, Any], th: RiskGateThresholds | None = None) -> float:
    snap = _as_snapshot(snapshot)
    t = th or RiskGateThresholds()

    # Piecewise linear normalization from warn->block to 0->1.
    def _norm(value: float, warn: float, block: float) -> float:
        v = float(value)
        w = float(warn)
        b = float(block)
        if b <= w:
            return 1.0 if v >= b else 0.0
        if v <= w:
            return 0.0
        return _clip01((v - w) / (b - w))

    parts = {
        "reject": _norm(snap.order_reject_rate, t.reject_rate_warn, t.reject_rate_block),
        "ws_lag": _norm(snap.ws_lag_ms, t.ws_lag_warn_ms, t.ws_lag_block_ms),
        "latency": _norm(snap.venue_latency_ms, t.venue_latency_warn_ms, t.venue_latency_block_ms),
        "drawdown": _norm(snap.drawdown_pct, t.drawdown_warn_pct, t.drawdown_block_pct),
        "leverage": _norm(snap.leverage, t.leverage_warn, t.leverage_block),
        "volatility": _norm(snap.realized_volatility, t.realized_vol_warn, t.realized_vol_block),
    }
    # Weighted stress score (0..1). Drawdown/latency get higher weight.
    weighted = (
        0.15 * parts["reject"]
        + 0.20 * parts["ws_lag"]
        + 0.20 * parts["latency"]
        + 0.25 * parts["drawdown"]
        + 0.10 * parts["leverage"]
        + 0.10 * parts["volatility"]
    )
    # Hard penalty when venue API is down.
    if not bool(snap.exchange_api_ok):
        weighted = max(weighted, 0.95)
    return _clip01(weighted)


def _has_any(hazards: Iterable[str], prefixes: tuple[str, ...]) -> bool:
    for h in hazards:
        s = str(h)
        for p in prefixes:
            if s.startswith(p):
                return True
    return False


def decide_gate(snapshot: RawSignalSnapshot | Dict[str, Any], th: RiskGateThresholds | None = None) -> RiskGateSignal:
    snap = _as_snapshot(snapshot)
    t = th or RiskGateThresholds()
    hazards = _hazards(snap, t)
    regime = classify_regime(snap, t)
    stress = compute_system_stress(snap, t)

    if "exchange_api_down" in hazards:
        gate = RiskGateState.FULL_STOP
        zone = "critical"
        reasons = ["venue_api_unavailable"]
    elif _has_any(hazards, ("drawdown_block", "ws_lag_block", "venue_latency_block", "volatility_block")):
        gate = RiskGateState.HALT_NEW_POSITIONS
        zone = "danger"
        reasons = ["block_threshold_breached"]
    elif _has_any(hazards, ("reject_rate_block", "leverage_block")):
        gate = RiskGateState.ALLOW_ONLY_REDUCTIONS
        zone = "stressed"
        reasons = ["execution_or_leverage_block"]
    elif _has_any(
        hazards,
        (
            "reject_rate_warn",
            "ws_lag_warn",
            "venue_latency_warn",
            "drawdown_warn",
            "leverage_warn",
            "volatility_warn",
        ),
    ):
        gate = RiskGateState.ALLOW_ONLY_REDUCTIONS
        zone = "caution"
        reasons = ["warn_threshold_breached"]
    elif stress >= 0.75:
        gate = RiskGateState.ALLOW_ONLY_REDUCTIONS
        zone = "stressed"
        reasons = ["high_stress_score"]
    else:
        gate = RiskGateState.ALLOW_TRADING
        zone = "stable"
        reasons = ["within_limits"]

    return RiskGateSignal(
        ts=snap.ts or _now_iso(),
        source="ops_intel",
        system_stress=float(stress),
        regime=str(regime),
        zone=str(zone),
        gate_state=gate,
        hazards=list(hazards),
        reasons=list(reasons),
    )


def process_snapshot(
    payload: RawSignalSnapshot | Dict[str, Any],
    *,
    store: OpsSignalStoreSQLite | None = None,
    thresholds: RiskGateThresholds | None = None,
) -> Dict[str, Any]:
    snap = payload if isinstance(payload, RawSignalSnapshot) else RawSignalSnapshot.from_dict(payload)
    gate = decide_gate(snap, th=thresholds)
    db = store or OpsSignalStoreSQLite()
    raw_id = db.insert_raw_signal(snap)
    gate_id = db.insert_risk_gate(gate)
    return {"ok": True, "raw_id": int(raw_id), "gate_id": int(gate_id), "gate": gate.to_dict()}
