from __future__ import annotations

from services.ops.live_signal_adapter import LiveSignalAdapter
from services.ops.risk_gate_contract import RiskGateState


def test_live_signal_adapter_publish_snapshot_with_gate(tmp_path):
    adapter = LiveSignalAdapter.from_default_db(path=str(tmp_path / "ops.sqlite"))
    out = adapter.publish_snapshot_with_gate(
        {
            "ts": "2026-03-09T00:00:00+00:00",
            "source": "bot",
            "exchange_api_ok": True,
            "order_reject_rate": 0.02,
            "ws_lag_ms": 100.0,
            "venue_latency_ms": 120.0,
            "realized_volatility": 0.01,
            "drawdown_pct": 1.0,
            "pnl_usd": 10.0,
            "exposure_usd": 1500.0,
            "leverage": 1.1,
        }
    )
    assert out["ok"] is True
    assert out["raw_id"] > 0
    assert out["gate_id"] > 0

    latest = adapter.latest_risk_gate()
    assert latest is not None
    assert latest["gate_state"] in {
        RiskGateState.ALLOW_TRADING.value,
        RiskGateState.ALLOW_ONLY_REDUCTIONS.value,
        RiskGateState.HALT_NEW_POSITIONS.value,
        RiskGateState.FULL_STOP.value,
    }
