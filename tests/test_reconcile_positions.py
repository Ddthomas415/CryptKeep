from __future__ import annotations

import json

import pytest

import scripts.reconcile_positions as reconcile_positions


def _install_invalid_reconcile_fakes(monkeypatch):
    import services.execution.live_exchange_adapter as live_exchange_adapter
    import storage.live_position_store_sqlite as live_position_store_sqlite

    class FakeAdapter:
        def __init__(self, venue, *, sandbox):
            assert venue == "coinbase"
            assert sandbox is True

        def fetch_balance(self):
            return {"total": {"BTC": "nan"}}

        def close(self):
            return None

    class FakeStore:
        def __init__(self, *, exec_db):
            assert exec_db

        def reconcile_to_exchange(self, *, venue, symbol, exchange_qty, tolerance):
            assert venue == "coinbase"
            assert symbol == "BTC/USD"
            assert str(exchange_qty).lower() == "nan"
            assert tolerance == 0.0001
            return {
                "ok": False,
                "venue": venue,
                "symbol": symbol,
                "local_qty": 0.0,
                "exchange_qty": None,
                "drift": None,
                "tolerance": None,
                "reason": "invalid_live_position_numeric:exchange_qty:exchange_qty_non_finite",
            }

    monkeypatch.setattr(live_exchange_adapter, "LiveExchangeAdapter", FakeAdapter)
    monkeypatch.setattr(live_position_store_sqlite, "LivePositionStore", FakeStore)


def test_parse_position_drift_threshold_rejects_nonfinite_or_negative():
    assert reconcile_positions.parse_position_drift_threshold("0.001") == 0.001
    assert reconcile_positions.parse_position_drift_threshold("nan") is None
    assert reconcile_positions.parse_position_drift_threshold("inf") is None
    assert reconcile_positions.parse_position_drift_threshold("-0.1") is None
    assert reconcile_positions.parse_position_drift_threshold("garbage") is None


def test_drift_for_flag_serializes_invalid_drift_as_null():
    assert reconcile_positions.drift_for_flag("0.25") == 0.25
    assert reconcile_positions.drift_for_flag(None) is None
    assert reconcile_positions.drift_for_flag("nan") is None
    assert reconcile_positions.drift_for_flag("garbage") is None


def test_main_rejects_invalid_threshold_before_exchange(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_VENUE", "coinbase")
    monkeypatch.setenv("CBP_SYMBOLS", "BTC/USD")
    monkeypatch.setenv("CBP_POSITION_DRIFT_THRESHOLD", "nan")

    with pytest.raises(SystemExit) as exc:
        reconcile_positions.main()

    assert exc.value.code == 2
    assert not (tmp_path / "data" / "risk_sink_failed.flag").exists()


def test_main_writes_flag_for_invalid_reconcile_result_without_crashing(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_VENUE", "coinbase")
    monkeypatch.setenv("CBP_SYMBOLS", "BTC/USD")
    monkeypatch.setenv("CBP_POSITION_DRIFT_THRESHOLD", "0.0001")

    _install_invalid_reconcile_fakes(monkeypatch)

    with pytest.raises(SystemExit) as exc:
        reconcile_positions.main()

    assert exc.value.code == 1
    payload = json.loads((tmp_path / "data" / "risk_sink_failed.flag").read_text(encoding="utf-8"))
    assert payload["drift"] is None
    assert "invalid_live_position_numeric:exchange_qty" in payload["error"]

    event_rows = (
        tmp_path / "data" / "operator_events" / "operator_events.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    assert len(event_rows) == 1
    event = json.loads(event_rows[0])
    assert event["action"] == "manual_reconcile"
    assert event["target"] == "position_drift_flag"
    assert event["result"] == "failed"
    assert event["reason"] == "position_drift_flag_written"
    assert event["pre_state"] == {"venue": "coinbase", "symbol": "BTC/USD"}
    assert event["post_state"]["drift"] is None
    assert "invalid_live_position_numeric:exchange_qty" in event["post_state"]["error"]


def test_main_writes_flag_when_operator_event_fails(monkeypatch, tmp_path, capsys):
    import services.audit.operator_event_journal as operator_event_journal

    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_VENUE", "coinbase")
    monkeypatch.setenv("CBP_SYMBOLS", "BTC/USD")
    monkeypatch.setenv("CBP_POSITION_DRIFT_THRESHOLD", "0.0001")
    _install_invalid_reconcile_fakes(monkeypatch)

    def _raise_operator_event(**_kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(operator_event_journal, "append_operator_event", _raise_operator_event)

    with pytest.raises(SystemExit) as exc:
        reconcile_positions.main()

    assert exc.value.code == 1
    payload = json.loads((tmp_path / "data" / "risk_sink_failed.flag").read_text(encoding="utf-8"))
    assert payload["fill_id"] == "position_drift"
    assert "invalid_live_position_numeric:exchange_qty" in payload["error"]
    captured = capsys.readouterr()
    assert "DRIFT DETECTED: risk_sink_failed.flag written" in captured.out
    assert (
        "WARNING: operator event failed: operator_event_write_failed:PermissionError"
        in captured.err
    )
