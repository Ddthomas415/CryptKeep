from __future__ import annotations

import math

import pytest

from storage.ws_status_sqlite import WSStatusSQLite


def test_ws_status_store_preserves_valid_zero_lag(tmp_path):
    db = WSStatusSQLite(path=tmp_path / "ws_status.sqlite")

    db.upsert_status(
        exchange="coinbase",
        symbol="BTC/USD",
        status="ok",
        recv_ts_ms=1_700_000_000_000,
        lag_ms=0.0,
        meta={"source": "test"},
    )

    row = db.get_status(exchange="coinbase", symbol="BTC/USD")
    assert row is not None
    assert row["recv_ts_ms"] == 1_700_000_000_000
    assert row["lag_ms"] == 0.0
    assert row["meta"] == {"source": "test"}
    assert len(db.recent_events(limit=10)) == 1


@pytest.mark.parametrize("recv_ts_ms", [0, -1, "nan"])
def test_ws_status_store_rejects_invalid_timestamp_before_mutation(tmp_path, recv_ts_ms):
    db = WSStatusSQLite(path=tmp_path / "ws_status.sqlite")

    with pytest.raises(ValueError, match="invalid_ws_status_numeric:recv_ts_ms"):
        db.upsert_status(
            exchange="coinbase",
            symbol="BTC/USD",
            status="ok",
            recv_ts_ms=recv_ts_ms,
            lag_ms=10.0,
        )

    assert db.get_status(exchange="coinbase", symbol="BTC/USD") is None
    assert db.recent_events(limit=10) == []


@pytest.mark.parametrize("lag_ms", [math.nan, float("inf"), -0.1, "garbage"])
def test_ws_status_store_rejects_invalid_lag_before_mutation(tmp_path, lag_ms):
    db = WSStatusSQLite(path=tmp_path / "ws_status.sqlite")

    with pytest.raises(ValueError, match="invalid_ws_status_numeric:lag_ms"):
        db.upsert_status(
            exchange="coinbase",
            symbol="BTC/USD",
            status="ok",
            recv_ts_ms=1_700_000_000_000,
            lag_ms=lag_ms,
        )

    assert db.get_status(exchange="coinbase", symbol="BTC/USD") is None
    assert db.recent_events(limit=10) == []
