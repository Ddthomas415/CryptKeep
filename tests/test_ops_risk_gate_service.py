from __future__ import annotations

import importlib

from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite


def _raw_snapshot(**kw):
    base = {
        "ts": "2026-03-09T00:00:00+00:00",
        "source": "bot",
        "exchange_api_ok": True,
        "order_reject_rate": 0.01,
        "ws_lag_ms": 100.0,
        "venue_latency_ms": 120.0,
        "realized_volatility": 0.01,
        "drawdown_pct": 1.0,
        "pnl_usd": 5.0,
        "exposure_usd": 1000.0,
        "leverage": 1.1,
    }
    base.update(kw)
    return base


def _reload_service(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.ops.risk_gate_service as svc

    importlib.reload(app_paths)
    importlib.reload(svc)
    return svc


def test_process_latest_raw_signal_no_data(monkeypatch, tmp_path):
    svc = _reload_service(monkeypatch, tmp_path)
    store = OpsSignalStoreSQLite(path=str(tmp_path / "ops.sqlite"))
    out = svc.process_latest_raw_signal(store=store)
    assert out["ok"] is False
    assert out["reason"] == "no_raw_signal"


def test_process_latest_raw_signal_writes_and_dedupes(monkeypatch, tmp_path):
    svc = _reload_service(monkeypatch, tmp_path)
    store = OpsSignalStoreSQLite(path=str(tmp_path / "ops.sqlite"))
    store.insert_raw_signal(_raw_snapshot())

    first = svc.process_latest_raw_signal(store=store)
    assert first["ok"] is True
    assert first["written"] is True
    assert first["gate_id"] > 0

    second = svc.process_latest_raw_signal(store=store)
    assert second["ok"] is True
    assert second["written"] is False
    assert second["reason"] == "unchanged"


def test_process_latest_raw_signal_write_if_unchanged(monkeypatch, tmp_path):
    svc = _reload_service(monkeypatch, tmp_path)
    store = OpsSignalStoreSQLite(path=str(tmp_path / "ops.sqlite"))
    store.insert_raw_signal(_raw_snapshot())
    one = svc.process_latest_raw_signal(store=store, write_if_unchanged=True)
    two = svc.process_latest_raw_signal(store=store, write_if_unchanged=True)
    assert one["written"] is True
    assert two["written"] is True


def test_run_forever_bounded_loops(monkeypatch, tmp_path):
    svc = _reload_service(monkeypatch, tmp_path)
    store = OpsSignalStoreSQLite(path=str(tmp_path / "ops.sqlite"))
    store.insert_raw_signal(_raw_snapshot())
    out = svc.run_forever(
        svc.RiskGateServiceCfg(store_path=str(tmp_path / "ops.sqlite"), poll_interval_sec=0.001, write_if_unchanged=False),
        max_loops=3,
    )
    assert out["ok"] is True
    assert out["loops"] == 3
    assert out["writes"] >= 1
    assert svc.STATUS_FILE.exists()


def test_request_stop_writes_flag(monkeypatch, tmp_path):
    svc = _reload_service(monkeypatch, tmp_path)
    out = svc.request_stop()
    assert out["ok"] is True
    assert svc.STOP_FILE.exists()
