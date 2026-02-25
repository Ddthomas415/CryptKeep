from __future__ import annotations

from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite


def test_ops_signal_store_roundtrip(tmp_path):
    db = str(tmp_path / "ops.sqlite")
    store = OpsSignalStoreSQLite(path=db)

    rid = store.insert_raw_signal(
        {
            "ts": "2026-02-25T00:00:00Z",
            "source": "bot",
            "exchange_api_ok": True,
            "order_reject_rate": 0.01,
            "ws_lag_ms": 24.0,
            "venue_latency_ms": 18.0,
            "realized_volatility": 0.22,
            "drawdown_pct": -2.1,
            "pnl_usd": 120.0,
            "exposure_usd": 6000.0,
            "leverage": 1.8,
            "extra": {"venue": "binance"},
        }
    )
    assert rid > 0

    latest_snap = store.latest_raw_signal()
    assert latest_snap is not None
    assert latest_snap["source"] == "bot"
    assert latest_snap["extra"]["venue"] == "binance"

    gid = store.insert_risk_gate(
        {
            "ts": "2026-02-25T00:01:00Z",
            "source": "ops_intel",
            "system_stress": 0.62,
            "regime": "volatile",
            "zone": "amber",
            "gate_state": "ALLOW_ONLY_REDUCTIONS",
            "hazards": ["ws_lag_spike"],
            "reasons": ["gate tightened"],
        }
    )
    assert gid > 0

    latest_gate = store.latest_risk_gate()
    assert latest_gate is not None
    assert latest_gate["gate_state"] == "ALLOW_ONLY_REDUCTIONS"
    assert latest_gate["hazards"] == ["ws_lag_spike"]

