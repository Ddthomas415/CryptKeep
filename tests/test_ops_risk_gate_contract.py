from __future__ import annotations

import pytest

from services.ops.risk_gate_contract import RiskGateSignal, RiskGateState, evaluate_gate_for_order


def test_evaluate_gate_allow_trading_allows_any_order():
    ok1, why1 = evaluate_gate_for_order(RiskGateState.ALLOW_TRADING, reduce_only=False)
    ok2, why2 = evaluate_gate_for_order(RiskGateState.ALLOW_TRADING, reduce_only=True)
    assert (ok1, why1) == (True, "ok")
    assert (ok2, why2) == (True, "ok")


def test_evaluate_gate_full_stop_blocks_all_orders():
    ok, why = evaluate_gate_for_order(RiskGateState.FULL_STOP, reduce_only=False)
    assert (ok, why) == (False, "full_stop")


def test_evaluate_gate_reduction_modes_require_reduce_only():
    for state in (RiskGateState.ALLOW_ONLY_REDUCTIONS, RiskGateState.HALT_NEW_POSITIONS):
        ok1, why1 = evaluate_gate_for_order(state, reduce_only=False)
        ok2, why2 = evaluate_gate_for_order(state, reduce_only=True)
        assert (ok1, why1) == (False, "reductions_only")
        assert (ok2, why2) == (True, "ok")


def test_risk_gate_signal_from_dict_roundtrip():
    payload = {
        "ts": "2026-02-25T00:00:00Z",
        "source": "ops_intel",
        "system_stress": 0.71,
        "regime": "high_vol",
        "zone": "fragile",
        "gate_state": "ALLOW_ONLY_REDUCTIONS",
        "hazards": ["ws_lag_spike", "reject_rate_rising"],
        "reasons": ["latency instability"],
    }
    sig = RiskGateSignal.from_dict(payload)
    out = sig.to_dict()
    assert out["gate_state"] == "ALLOW_ONLY_REDUCTIONS"
    assert out["regime"] == "high_vol"
    assert out["hazards"] == ["ws_lag_spike", "reject_rate_rising"]


def test_risk_gate_signal_rejects_unknown_gate():
    with pytest.raises(ValueError):
        RiskGateSignal.from_dict({"gate_state": "NOT_A_REAL_GATE"})

