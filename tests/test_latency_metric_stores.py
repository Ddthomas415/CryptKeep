from __future__ import annotations

import math
import sqlite3

import pytest

from storage.latency_metrics_sqlite import LatencyMetricsSQLite
from storage.market_ws_store_sqlite import SQLiteMarketWsStore


def _market_ws_rows(path) -> list[tuple]:
    con = sqlite3.connect(str(path))
    try:
        return con.execute(
            "SELECT ts_ms, category, name, value_ms, meta_json FROM market_ws_latency"
        ).fetchall()
    finally:
        con.close()


def test_latency_metrics_store_preserves_valid_zero_latency(tmp_path):
    db = LatencyMetricsSQLite(path=tmp_path / "latency.sqlite")

    db.log_latency(
        ts_ms=1_700_000_000_000,
        category="execution",
        name="order_submit_ms",
        value_ms=0.0,
        meta={"source": "test"},
    )

    rows = db.recent(limit=10)
    assert len(rows) == 1
    assert rows[0]["ts_ms"] == 1_700_000_000_000
    assert rows[0]["value_ms"] == 0.0
    assert rows[0]["meta"] == {"source": "test"}
    assert db.rolling_p95(category="execution", name="order_submit_ms")["p95_ms"] == 0.0


@pytest.mark.parametrize("ts_ms", [0, -1, "nan"])
def test_latency_metrics_store_rejects_invalid_timestamp_before_mutation(tmp_path, ts_ms):
    db = LatencyMetricsSQLite(path=tmp_path / "latency.sqlite")

    with pytest.raises(ValueError, match="invalid_latency_metric_numeric:ts_ms"):
        db.log_latency(
            ts_ms=ts_ms,
            category="execution",
            name="submit_to_ack_ms",
            value_ms=10.0,
        )

    assert db.recent(limit=10) == []


@pytest.mark.parametrize("value_ms", [math.nan, float("inf"), -0.1, "garbage"])
def test_latency_metrics_store_rejects_invalid_value_before_mutation(tmp_path, value_ms):
    db = LatencyMetricsSQLite(path=tmp_path / "latency.sqlite")

    with pytest.raises(ValueError, match="invalid_latency_metric_numeric:value_ms"):
        db.log_latency(
            ts_ms=1_700_000_000_000,
            category="execution",
            name="submit_to_ack_ms",
            value_ms=value_ms,
        )

    assert db.recent(limit=10) == []


def test_market_ws_store_preserves_valid_zero_latency(tmp_path):
    path = tmp_path / "market_ws.sqlite"
    db = SQLiteMarketWsStore(path=path)

    db.log_latency(
        ts_ms=1_700_000_000_000,
        category="execution",
        name="order_submit_ms",
        value_ms=0.0,
        meta={"source": "test"},
    )

    rows = _market_ws_rows(path)
    assert len(rows) == 1
    assert rows[0][0] == 1_700_000_000_000
    assert rows[0][3] == 0.0


@pytest.mark.parametrize("ts_ms", [0, -1, "nan"])
def test_market_ws_store_rejects_invalid_timestamp_before_mutation(tmp_path, ts_ms):
    path = tmp_path / "market_ws.sqlite"
    db = SQLiteMarketWsStore(path=path)

    with pytest.raises(ValueError, match="invalid_market_ws_latency_numeric:ts_ms"):
        db.log_latency(
            ts_ms=ts_ms,
            category="execution",
            name="submit_to_ack_ms",
            value_ms=10.0,
        )

    assert _market_ws_rows(path) == []


@pytest.mark.parametrize("value_ms", [math.nan, float("inf"), -0.1, "garbage"])
def test_market_ws_store_rejects_invalid_value_before_mutation(tmp_path, value_ms):
    path = tmp_path / "market_ws.sqlite"
    db = SQLiteMarketWsStore(path=path)

    with pytest.raises(ValueError, match="invalid_market_ws_latency_numeric:value_ms"):
        db.log_latency(
            ts_ms=1_700_000_000_000,
            category="execution",
            name="submit_to_ack_ms",
            value_ms=value_ms,
        )

    assert _market_ws_rows(path) == []
