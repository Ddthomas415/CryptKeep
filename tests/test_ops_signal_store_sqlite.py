from __future__ import annotations

import json
import math
import sqlite3

import pytest

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


def _valid_raw_snapshot(**overrides):
    payload = {
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
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("order_reject_rate", math.nan),
        ("ws_lag_ms", float("inf")),
        ("venue_latency_ms", -1.0),
        ("realized_volatility", -0.01),
        ("pnl_usd", float("nan")),
        ("exposure_usd", -1.0),
        ("leverage", float("inf")),
    ],
)
def test_ops_signal_store_rejects_invalid_raw_signal_before_mutation(tmp_path, field, value):
    store = OpsSignalStoreSQLite(path=str(tmp_path / "ops.sqlite"))

    with pytest.raises(ValueError, match=f"invalid_ops_signal_numeric:{field}"):
        store.insert_raw_signal(_valid_raw_snapshot(**{field: value}))

    assert store.latest_raw_signal() is None


def test_ops_signal_store_rejects_invalid_gate_signal_before_mutation(tmp_path):
    store = OpsSignalStoreSQLite(path=str(tmp_path / "ops.sqlite"))

    with pytest.raises(ValueError, match="invalid_ops_signal_numeric:system_stress"):
        store.insert_risk_gate(
            {
                "ts": "2026-02-25T00:01:00Z",
                "source": "ops_intel",
                "system_stress": float("nan"),
                "regime": "volatile",
                "zone": "amber",
                "gate_state": "ALLOW_ONLY_REDUCTIONS",
                "hazards": ["ws_lag_spike"],
                "reasons": ["gate tightened"],
            }
        )

    assert store.latest_risk_gate() is None


def test_ops_risk_gate_service_fails_closed_on_persisted_corrupt_raw_signal(tmp_path):
    import services.ops.risk_gate_service as svc

    db_path = tmp_path / "ops.sqlite"
    store = OpsSignalStoreSQLite(path=str(db_path))
    payload = _valid_raw_snapshot(ws_lag_ms=math.nan)
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "INSERT INTO ops_raw_signal_snapshots(ts, source, payload_json) VALUES(?,?,?)",
            (payload["ts"], payload["source"], json.dumps(payload)),
        )
        con.commit()
    finally:
        con.close()

    out = svc.process_latest_raw_signal(store=store, write_if_unchanged=True)

    assert out["ok"] is True
    assert out["written"] is True
    gate = out["gate"]
    assert gate["gate_state"] == "FULL_STOP"
    assert gate["zone"] == "critical"
    assert gate["hazards"] == ["ops_raw_signal_invalid"]
    assert gate["reasons"] == ["invalid_ops_signal_numeric:ws_lag_ms"]
