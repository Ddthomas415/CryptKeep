from __future__ import annotations

import pytest

from services.execution import place_order as po


def test_ops_gate_disabled_does_not_block(monkeypatch):
    monkeypatch.delenv("CBP_OPS_RISK_GATE_ENFORCE", raising=False)
    po._enforce_ops_risk_gate(params={})


def test_ops_gate_full_stop_blocks(monkeypatch):
    monkeypatch.setenv("CBP_OPS_RISK_GATE_ENFORCE", "1")
    monkeypatch.delenv("CBP_OPS_RISK_GATE_FAIL_CLOSED", raising=False)
    monkeypatch.setattr(
        po,
        "_load_latest_ops_risk_gate",
        lambda: {
            "ts": "2026-02-25T00:01:00Z",
            "source": "ops_intel",
            "system_stress": 0.9,
            "regime": "panic",
            "zone": "red",
            "gate_state": "FULL_STOP",
            "hazards": ["exchange_unstable"],
            "reasons": ["hard stop"],
        },
    )
    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:ops_risk_gate:full_stop"):
        po._enforce_ops_risk_gate(params={})


def test_ops_gate_reductions_only_allows_reduce_only(monkeypatch):
    monkeypatch.setenv("CBP_OPS_RISK_GATE_ENFORCE", "1")
    monkeypatch.setattr(
        po,
        "_load_latest_ops_risk_gate",
        lambda: {
            "ts": "2026-02-25T00:02:00Z",
            "source": "ops_intel",
            "system_stress": 0.7,
            "regime": "volatile",
            "zone": "amber",
            "gate_state": "ALLOW_ONLY_REDUCTIONS",
            "hazards": ["drawdown_risk"],
            "reasons": ["tightened gate"],
        },
    )
    po._enforce_ops_risk_gate(params={"reduceOnly": True})
    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:ops_risk_gate:reductions_only"):
        po._enforce_ops_risk_gate(params={})


def test_ops_gate_fail_closed_blocks_when_signal_missing(monkeypatch):
    monkeypatch.setenv("CBP_OPS_RISK_GATE_ENFORCE", "1")
    monkeypatch.setenv("CBP_OPS_RISK_GATE_FAIL_CLOSED", "1")
    monkeypatch.setattr(po, "_load_latest_ops_risk_gate", lambda: None)
    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:ops_risk_gate_missing"):
        po._enforce_ops_risk_gate(params={})

