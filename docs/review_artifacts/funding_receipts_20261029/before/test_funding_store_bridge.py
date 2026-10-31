from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
from threading import Barrier

import pytest

from services.analytics.funding_observations import encoded, identity, observation
from storage import crypto_edge_store_sqlite as storage


ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "docs/review_artifacts/funding_store_bridge_20261029/before/crypto_edge_store_sqlite.py"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("external boundary forbidden")
    original = sqlite3.connect
    def temporary_connect(database, *args, **kwargs):
        assert Path(database).resolve().is_relative_to(tmp_path.resolve())
        return original(database, *args, **kwargs)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(storage, "ensure_dirs", refuse)
    monkeypatch.setattr(sqlite3, "connect", temporary_connect)


@pytest.fixture
def inputs():
    return {"venue": "okx", "symbol": "EXAMPLE/USDT:USDT",
            "captured_at": "2026-10-29T01:00:00Z",
            "payload": {"nextFundingRate": "-0.0001",
                        "timestamp": 1700000000000,
                        "info": {"fundingTime": "1700003600000"}}}


@pytest.fixture
def store(tmp_path):
    return storage.CryptoEdgeStoreSQLite(path=str(tmp_path / "disposable.sqlite"))


def write(store, rows, source="synthetic", **budgets):
    return store.append_raw_funding_observations(
        rows, source=source, **({"max_rows": 10, "max_bytes": 32768} | budgets))


def read(store, source="synthetic", limit=100):
    return store.recent_raw_funding_observations(source=source, limit=limit)


def test_promoted_decoder_is_exact_reviewed_source():
    current = (ROOT / "services/analytics/funding_observations.py").read_bytes()
    assert hashlib.sha256(current).hexdigest() == "e884234f22607b551fa81d662d192ad9bb9e4b72e0a7466825114c6d44a7df89"


def test_unknown_roundtrips_after_store_reopen_without_normalized_rows(store, inputs):
    original = deepcopy(inputs)
    result = write(store, [inputs])
    assert result["inserted"] == 1 and result["normalization_eligible"] is False
    reopened = storage.CryptoEdgeStoreSQLite(path=store.path)
    saved = read(reopened)
    assert saved["legacy_included"] is False and saved["normalization_eligible"] is False
    record = saved["observations"][0]["observation"]
    assert record["raw_payload"] == original["payload"]
    assert record["interval_hours"] is None and record["rate_kind"] == "predicted"
    assert record["rate_source_field"] == "nextFundingRate"
    assert record["reported_exchange_time_fields"]["info.fundingTime"] == "1700003600000"
    assert record["normalization"]["annualized_pct"] is None
    assert reopened.latest_funding_rows() == []
    assert reopened.latest_report()["funding"]["count"] == 0
    assert inputs == original


@pytest.mark.parametrize("interval", ["1h", "4h", "8h"])
def test_known_interval_stays_unscored_without_formula(store, inputs, interval):
    inputs["payload"]["interval"] = interval
    write(store, [inputs])
    record = read(store)["observations"][0]["observation"]
    assert record["interval_hours"] == int(interval[:-1])
    assert record["normalization"]["eligible"] is False
    assert record["normalization"]["reason"] == "formula_basis_unverified"


def test_existing_schema_and_legacy_rows_remain_unchanged(tmp_path, inputs):
    tree = ast.parse(BEFORE.read_bytes())
    ddl = next(n.value.value for n in tree.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "DDL" for t in n.targets))
    path = tmp_path / "old.sqlite"
    with sqlite3.connect(path) as conn:
        conn.executescript(ddl)
        payload = {"symbol": "LEGACY", "venue": "okx", "funding_rate": 0.0001, "interval_hours": 8}
        conn.execute("INSERT INTO funding_snapshots "
                     "(snapshot_id,capture_ts,source,symbol,venue,funding_rate,interval_hours,payload_json) "
                     "VALUES(?,?,?,?,?,?,?,?)",
                     ("legacy", "2026-10-28T00:00:00Z", "synthetic", "LEGACY", "okx", 0.0001, 8, encoded(payload)))
        before = conn.execute("SELECT * FROM funding_snapshots").fetchall()
        before_schema = conn.execute("SELECT sql FROM sqlite_master WHERE name='funding_snapshots'").fetchone()
    store = storage.CryptoEdgeStoreSQLite(path=str(path))
    write(store, [inputs])
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT * FROM funding_snapshots").fetchall() == before
        assert conn.execute("SELECT sql FROM sqlite_master WHERE name='funding_snapshots'").fetchone() == before_schema
    assert store.latest_funding_rows() == [payload]
    assert len(read(store)["observations"]) == 1
    assert read(store)["legacy_included"] is False


def test_same_content_is_idempotent_and_sources_are_separate(store, inputs):
    first = write(store, [inputs, inputs])
    assert (first["inserted"], first["duplicates"]) == (1, 1)
    assert write(store, [inputs])["inserted"] == 0
    assert write(store, [inputs], source="other")["inserted"] == 1
    assert len(read(store)["observations"]) == 1
    assert len(read(store, source="other")["observations"]) == 1
    assert read(store, source="absent")["observations"] == []


def test_changed_evidence_appends_and_timezones_sort_by_actual_time(store, inputs):
    first = deepcopy(inputs)
    first["captured_at"] = "2026-10-29T02:00:00+02:00"
    second = deepcopy(inputs)
    second["captured_at"] = "2026-10-29T00:30:00Z"
    write(store, [first, second])
    rows = read(store)["observations"]
    assert [r["observation"]["captured_at"] for r in rows] == [
        second["captured_at"], first["captured_at"]]
    assert rows[0]["observation_key"] != rows[1]["observation_key"]
    assert len(read(store, limit=1)["observations"]) == 1


@pytest.mark.parametrize("budgets", [{"max_rows": 0}, {"max_rows": True}, {"max_bytes": 0},
                                    {"max_bytes": True}, {"max_rows": 1}, {"max_bytes": 1}])
def test_explicit_budgets_refuse_whole_batch(store, inputs, budgets):
    with pytest.raises(ValueError, match="budget"):
        write(store, [inputs, inputs], **budgets)
    assert read(store)["observations"] == []


def test_invalid_later_input_cannot_partially_append(store, inputs):
    bad = deepcopy(inputs)
    bad["captured_at"] = "no timezone or date"
    with pytest.raises(ValueError):
        write(store, [inputs, bad])
    assert read(store)["observations"] == []


def test_insert_failure_rolls_back_entire_batch(store, inputs):
    other = deepcopy(inputs)
    other["payload"]["nextFundingRate"] = "-0.0002"
    second_key = identity(observation(**other))
    with sqlite3.connect(store.path) as conn:
        conn.execute("CREATE TRIGGER refuse_second BEFORE INSERT ON raw_funding_observations "
                     "WHEN NEW.observation_key='" + second_key + "' "
                     "BEGIN SELECT RAISE(ABORT, 'invented failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="invented failure"):
        write(store, [inputs, other])
    assert read(store)["observations"] == []


def test_corrupt_duplicate_is_preserved_and_refused(store, inputs):
    key = identity(observation(**inputs))
    with sqlite3.connect(store.path) as conn:
        conn.execute("INSERT INTO raw_funding_observations"
                     "(source,observation_key,capture_ts,payload_json) VALUES(?,?,?,?)",
                     ("synthetic", key, "wrong time", "{}"))
    with pytest.raises(ValueError, match="stored_raw_funding_conflict"):
        write(store, [inputs])
    with pytest.raises(ValueError, match="stored_raw_funding_corrupt"):
        read(store)
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT payload_json FROM raw_funding_observations").fetchone()[0] == "{}"


def test_rehashed_normalization_forgery_is_not_returned(store, inputs):
    forged = observation(**inputs)
    forged["normalization"]["eligible"] = True
    with sqlite3.connect(store.path) as conn:
        conn.execute("INSERT INTO raw_funding_observations"
                     "(source,observation_key,capture_ts,payload_json) VALUES(?,?,?,?)",
                     ("synthetic", identity(forged), "2026-10-29T01:00:00+00:00", encoded(forged)))
    with pytest.raises(ValueError, match="stored_raw_funding_corrupt"):
        read(store)


@pytest.mark.parametrize("source", ["", " spaced ", None, 1])
def test_source_is_explicit_and_not_silently_normalized(store, inputs, source):
    with pytest.raises(ValueError, match="source"):
        write(store, [inputs], source=source)
    with pytest.raises(ValueError, match="source"):
        read(store, source=source)


@pytest.mark.parametrize("limit", [0, -1, True, None])
def test_reader_limit_is_explicit(store, limit):
    with pytest.raises(ValueError, match="limit"):
        read(store, limit=limit)


def test_concurrent_identical_appends_have_one_insert(store, inputs):
    barrier = Barrier(2, timeout=3)
    def append():
        barrier.wait()
        return write(store, [inputs])
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(append) for _ in range(2)]
        results = [future.result(timeout=5) for future in futures]
    assert sum(r["inserted"] for r in results) == 1
    assert len(read(store)["observations"]) == 1
