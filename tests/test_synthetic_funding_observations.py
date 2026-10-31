from copy import deepcopy
import json
import socket
import sqlite3

import pytest

from scripts.research.synthetic_funding_observations import (
    append_observation, encoded, identity, observation, read_observation,
)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


@pytest.fixture
def inputs():
    return {"venue": "okx", "symbol": "EXAMPLE/USDT:USDT",
            "captured_at": "2026-10-28T12:00:00Z", "payload": {"fundingRate": "0.0001"}}


def fixture_connection(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE live_consumer_state(k TEXT PRIMARY KEY, v TEXT NOT NULL)")
    conn.commit()
    return conn


def test_unknown_is_preserved_without_eight_hour_or_neutral_substitution(inputs):
    record = observation(**inputs, plan_interval_hours=8)
    assert record["interval_hours"] is None
    assert record["interval_issue"] == "interval_unknown"
    assert record["normalization"] == {"eligible": False, "reason": "interval_unknown",
                                       "rate_per_8h": None, "annualized_pct": None}
    assert record["plan_interval_hours_unverified"] == 8
    assert "signal" not in record
    assert record["execution_authority"] is False


@pytest.mark.parametrize("hours", [1, 4, 8])
def test_explicit_interval_does_not_certify_formula_or_settled_rate(inputs, hours):
    inputs["payload"]["interval"] = str(hours) + "h"
    record = observation(**inputs)
    assert record["interval_hours"] == hours
    assert record["interval_source_fields"] == ["interval"]
    assert record["rate_kind"] == "unknown"
    assert record["rate_kind_verified"] is False
    assert record["normalization"]["reason"] == "formula_basis_unverified"
    assert record["normalization"]["annualized_pct"] is None


@pytest.mark.parametrize("source", ["nextFundingRate", "next_funding_rate"])
def test_predicted_origin_and_raw_timestamps_survive(inputs, source):
    inputs["payload"] = {source: "-0.0001", "timestamp": 1700000000000,
                         "nextFundingTimestamp": 1700003600000,
                         "info": {"fundingTime": "1700003600000"}}
    original = deepcopy(inputs["payload"])
    record = observation(**inputs)
    assert record["raw_payload"] == original
    assert record["rate_source_field"] == source and record["rate_kind"] == "predicted"
    assert record["reported_exchange_time_fields"] == {
        "timestamp": 1700000000000, "nextFundingTimestamp": 1700003600000,
        "info.fundingTime": "1700003600000"}
    assert record["captured_at"] == inputs["captured_at"]
    inputs["payload"]["info"]["fundingTime"] = "changed"
    assert record["raw_payload"] == original


@pytest.mark.parametrize("value", [0, -1, True, "nan", "inf", "abc", "1d", 4])
def test_bad_interval_is_kept_raw_but_not_normalized(inputs, value):
    inputs["payload"]["interval"] = value
    record = observation(**inputs)
    assert record["raw_payload"]["interval"] == value
    assert record["interval_hours"] is None
    assert record["normalization"]["reason"] == "interval_invalid"


def test_conflicting_interval_sources_are_not_cherry_picked(inputs):
    inputs["payload"].update(interval="1h", info={"fundingIntervalHours": "8"})
    record = observation(**inputs)
    assert record["interval_issue"] == "interval_conflict"
    assert record["interval_hours"] is None


@pytest.mark.parametrize("value", [None, True, "nan", "inf", "bad"])
def test_missing_or_invalid_rate_stays_unscored(inputs, value):
    inputs["payload"]["fundingRate"] = value
    record = observation(**inputs)
    assert record["funding_rate"] is None
    assert record["normalization"]["reason"] == "rate_unknown"
    assert record["raw_payload"] == inputs["payload"]


def test_zero_rate_is_not_missing(inputs):
    inputs["payload"]["fundingRate"] = 0
    assert observation(**inputs)["funding_rate"] == 0


def test_duplicate_append_is_idempotent_and_unknown_survives_reopen(tmp_path, inputs):
    path = tmp_path / "disposable.sqlite"
    conn = fixture_connection(path)
    try:
        first = append_observation(conn, max_bytes=8192, **inputs)
        second = append_observation(conn, max_bytes=8192, **inputs)
        assert first["inserted"] is True and second["inserted"] is False
        assert conn.execute("SELECT count(*) FROM live_consumer_state").fetchone()[0] == 1
    finally:
        conn.close()
    with sqlite3.connect(path) as reopened:
        record = read_observation(reopened, first["key"])
        assert record == first["observation"]
        assert record["interval_hours"] is None
        assert record["normalization"]["eligible"] is False


def test_changes_append_new_evidence_and_do_not_overwrite(inputs):
    with fixture_connection() as conn:
        first = append_observation(conn, max_bytes=8192, **inputs)
        inputs["payload"]["interval"] = "4h"
        second = append_observation(conn, max_bytes=8192, **inputs)
        assert first["key"] != second["key"]
        assert read_observation(conn, first["key"])["interval_hours"] is None
        assert read_observation(conn, second["key"])["interval_hours"] == 4


def test_no_implicit_schema_or_caller_transaction_commit(inputs):
    with sqlite3.connect(":memory:") as empty:
        with pytest.raises(sqlite3.OperationalError, match="no such table"):
            append_observation(empty, max_bytes=8192, **inputs)
        assert empty.in_transaction is False
        assert empty.execute("SELECT name FROM sqlite_master").fetchall() == []
    with fixture_connection() as conn:
        conn.execute("INSERT INTO live_consumer_state VALUES('other','pending')")
        with pytest.raises(ValueError, match="caller_transaction"):
            append_observation(conn, max_bytes=8192, **inputs)
        assert conn.in_transaction is True
        conn.rollback()
        assert conn.execute("SELECT * FROM live_consumer_state").fetchall() == []


def test_insert_failure_rolls_back_and_preserves_other_namespaces(inputs):
    with fixture_connection() as conn:
        conn.execute("INSERT INTO live_consumer_state VALUES('existing','unchanged')")
        conn.execute("CREATE TRIGGER refuse BEFORE INSERT ON live_consumer_state "
                     "BEGIN SELECT RAISE(ABORT, 'invented failure'); END")
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="invented failure"):
            append_observation(conn, max_bytes=8192, **inputs)
        assert conn.in_transaction is False
        assert conn.execute("SELECT * FROM live_consumer_state").fetchall() == [("existing", "unchanged")]


def test_conflicting_or_corrupt_stored_evidence_is_not_repaired_or_overwritten(inputs):
    record = observation(**inputs)
    key = identity(record)
    with fixture_connection() as conn:
        conn.execute("INSERT INTO live_consumer_state VALUES(?,?)", (key, "{}"))
        conn.commit()
        with pytest.raises(ValueError, match="stored_observation_conflict"):
            append_observation(conn, max_bytes=8192, **inputs)
        with pytest.raises(ValueError, match="stored_observation_corrupt"):
            read_observation(conn, key)
        assert conn.execute("SELECT v FROM live_consumer_state").fetchone()[0] == "{}"


@pytest.mark.parametrize("budget", [0, -1, True, 1])
def test_byte_budget_is_explicit_and_blocks_before_writes(inputs, budget):
    with fixture_connection() as conn:
        with pytest.raises(ValueError, match="budget"):
            append_observation(conn, max_bytes=budget, **inputs)
        assert conn.execute("SELECT * FROM live_consumer_state").fetchall() == []


@pytest.mark.parametrize("captured", ["", "2026-10-28T12:00:00", "not a date"])
def test_capture_requires_explicit_timezone(inputs, captured):
    inputs["captured_at"] = captured
    with pytest.raises(ValueError):
        observation(**inputs)


def test_non_json_nonfinite_input_fails_instead_of_truncation(inputs):
    inputs["payload"]["fundingRate"] = float("nan")
    with pytest.raises(ValueError):
        observation(**inputs)


def test_raw_nested_payload_and_unknown_fields_roundtrip_exactly(inputs):
    inputs["payload"]["info"] = {"future_public_field": ["value", {"nested": 0}]}
    with fixture_connection() as conn:
        result = append_observation(conn, max_bytes=8192, **inputs)
        record = read_observation(conn, result["key"])
        assert json.loads(encoded(record["raw_payload"])) == inputs["payload"]
