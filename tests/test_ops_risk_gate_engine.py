from __future__ import annotations

from services.ops.risk_gate_contract import RiskGateState
from services.ops.risk_gate_engine import RiskGateThresholds, decide_gate, process_snapshot
from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite


def _base_snapshot() -> dict:
    return {
        "ts": "2026-03-09T00:00:00+00:00",
        "source": "bot",
        "exchange_api_ok": True,
        "order_reject_rate": 0.01,
        "ws_lag_ms": 100.0,
        "venue_latency_ms": 80.0,
        "realized_volatility": 0.01,
        "drawdown_pct": 1.5,
        "pnl_usd": 5.0,
        "exposure_usd": 1000.0,
        "leverage": 1.2,
    }


def test_decide_gate_allow_trading_under_normal_conditions():
    gate = decide_gate(_base_snapshot())
    assert gate.gate_state == RiskGateState.ALLOW_TRADING
    assert gate.zone == "stable"
    assert gate.system_stress < 0.75


def test_decide_gate_full_stop_when_exchange_api_down():
    payload = _base_snapshot()
    payload["exchange_api_ok"] = False
    gate = decide_gate(payload)
    assert gate.gate_state == RiskGateState.FULL_STOP
    assert "exchange_api_down" in gate.hazards
    assert gate.system_stress >= 0.95


def test_decide_gate_halt_new_positions_on_block_latency():
    payload = _base_snapshot()
    payload["ws_lag_ms"] = 4000.0
    gate = decide_gate(payload)
    assert gate.gate_state == RiskGateState.HALT_NEW_POSITIONS
    assert "ws_lag_block" in gate.hazards


def test_decide_gate_reductions_only_on_warn_drawdown():
    payload = _base_snapshot()
    payload["drawdown_pct"] = 7.0
    gate = decide_gate(payload)
    assert gate.gate_state == RiskGateState.ALLOW_ONLY_REDUCTIONS
    assert gate.zone in ("caution", "stressed")
    assert "drawdown_warn" in gate.hazards


def test_process_snapshot_persists_raw_and_gate(tmp_path):
    store = OpsSignalStoreSQLite(path=str(tmp_path / "ops.sqlite"))
    out = process_snapshot(_base_snapshot(), store=store, thresholds=RiskGateThresholds())
    assert out["ok"] is True
    assert out["raw_id"] > 0
    assert out["gate_id"] > 0
    latest_raw = store.latest_raw_signal()
    latest_gate = store.latest_risk_gate()
    assert latest_raw is not None
    assert latest_gate is not None
    assert latest_raw["source"] == "bot"
    assert latest_gate["source"] == "ops_intel"
    assert latest_gate["gate_state"] in {
        RiskGateState.ALLOW_TRADING.value,
        RiskGateState.ALLOW_ONLY_REDUCTIONS.value,
        RiskGateState.HALT_NEW_POSITIONS.value,
        RiskGateState.FULL_STOP.value,
    }
