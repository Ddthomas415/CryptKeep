from __future__ import annotations

import ast
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import count
from pathlib import Path
import socket
import sqlite3

import pytest

from services.analytics.funding_observations import observation
from scripts.research.synthetic_funding_observations import observation as frozen
from services.analytics.funding_observations import encoded, identity
from storage import crypto_edge_store_sqlite as storage


ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "docs/review_artifacts/funding_receipts_20261029/before"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("external boundary forbidden")
    connect = sqlite3.connect
    def temporary(database, *args, **kwargs):
        assert Path(database).resolve().is_relative_to(tmp_path.resolve())
        return connect(database, *args, **kwargs)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(sqlite3, "connect", temporary)
    monkeypatch.setattr(storage, "ensure_dirs", refuse)


def selected(path, functions, ns, classes=()):
    tree = ast.parse(path.read_bytes())
    nodes = [n for n in tree.body if (
        isinstance(n, ast.FunctionDef) and n.name in functions
        or isinstance(n, ast.ClassDef) and n.name in classes)]
    assert {n.name for n in nodes} == set(functions) | set(classes)
    ns["__name__"] = __name__
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), "exec"), ns)
    return ns


def collector(payload, *, old=False, failure=None):
    trace = []
    ticks = count()
    base = datetime(2026, 10, 29, tzinfo=timezone.utc)
    class Fake:
        def fetch_funding_rate(self, symbol):
            trace.append(("fetch", symbol))
            if failure:
                raise failure
            return payload
    ns = {"defaultdict": defaultdict, "observation": observation,
          "normalize_venue": lambda value: value.lower(),
          "map_symbol": lambda venue, symbol: "native:" + symbol,
          "_open_public_exchange": lambda venue: Fake(),
          "_close_exchange": lambda ex: trace.append("close"),
          "_funding_received_at": lambda: (base + timedelta(seconds=next(ticks))).isoformat()}
    for name in ("open_interest", "basis", "quote", "order_book"):
        ns["_collect_" + name + "_rows"] = lambda rows: ([], [])
    path = BEFORE / "crypto_edge_collector.py" if old else ROOT / "services/analytics/crypto_edge_collector.py"
    names = {"_extract_funding_rate", "_collect_funding_rows", "collect_live_crypto_edge_snapshot"}
    if not old:
        names.add("_collect_funding_observations")
    selected(path, names, ns)
    return ns["collect_live_crypto_edge_snapshot"], trace, ns


PLAN = {"funding": [{"venue": "okx", "symbol": "EXAMPLE", "interval_hours": 8}]}


def service(plan, fetch, path, *, old=False, store_class=storage.CryptoEdgeStoreSQLite):
    ns = {"dataclass": dataclass, "_load_plan": lambda filename: deepcopy(plan),
          "collect_live_crypto_edge_snapshot": fetch, "CryptoEdgeStoreSQLite": store_class}
    source = BEFORE / "crypto_edge_collector_service.py" if old else ROOT / "services/analytics/crypto_edge_collector_service.py"
    selected(source, {"collect_once"}, ns, {"CryptoEdgeCollectorServiceCfg"})
    def run(**kwargs):
        cfg = ns["CryptoEdgeCollectorServiceCfg"](plan_file="not-opened", db_path=str(path), **kwargs)
        return ns["collect_once"](cfg)
    return run


@pytest.mark.parametrize("interval", [None, "1h", "4h", "8h"])
def test_raw_fetch_receipt_to_sqlite_does_not_feed_legacy_estimates(tmp_path, interval):
    payload = {"symbol": "native:EXAMPLE", "nextFundingRate": "0.0001",
               "fundingTimestamp": 1700003600000,
               "info": {"time": 1700000000000, "fundingTime": "1700003600000",
                        "nextFundingRate": "0.0001"}}
    if interval:
        payload["interval"] = interval
    original = deepcopy(payload)
    fetch, trace, _ = collector(payload)
    path = tmp_path / "journal.sqlite"
    store = storage.CryptoEdgeStoreSQLite(path=str(path))
    store.append_funding_rows([{"symbol": "OLD", "venue": "okx", "funding_rate": 0.1}],
                              source="live_public", snapshot_id="old")
    run = service(PLAN, fetch, path)
    out = run(raw_funding_only=True, raw_funding_max_rows=2, raw_funding_max_bytes=32768)
    assert trace == [("fetch", "native:EXAMPLE"), "close"]
    assert payload == original
    assert out["ok"] is True and out["raw_funding_count"] == 1 and out["funding_count"] == 0
    assert "funding_snapshot_id" not in out
    assert out["report"]["funding"]["annualized_carry_pct"] is None
    assert out["report"]["funding"]["dominant_bias"] == "unknown"
    assert out["report"]["funding_meta"] is None and out["report"]["funding_legacy_excluded"] is True
    reopened = storage.CryptoEdgeStoreSQLite(path=str(path))
    record = reopened.recent_raw_funding_observations(source="live_public", limit=2)["observations"][0]["observation"]
    assert record["schema"] == 2 and record["raw_payload"] == original
    assert record["captured_at"] == "2026-10-29T00:00:01+00:00"
    assert record["receipt"]["request_started_at"] == "2026-10-29T00:00:00+00:00"
    assert record["receipt"]["received_at"] == record["captured_at"]
    assert record["receipt"]["requested_symbol"] == "native:EXAMPLE"
    assert record["receipt"]["response_symbol_matches_request"] is True
    assert record["receipt"]["native_to_unified_mapping_verified"] is False
    assert record["reported_exchange_time_fields"]["info.time"] == 1700000000000
    assert record["normalization"]["eligible"] is False
    assert record["interval_hours"] == (int(interval[:-1]) if interval else None)
    assert len(reopened.latest_funding_rows()) == 1
    assert reopened.latest_funding_rows()[0]["symbol"] == "OLD"


@pytest.mark.parametrize("payload", [{}, {"fundingRate": "nan"}, {"nextFundingRate": "bad"}])
def test_json_payload_with_unknown_rate_is_preserved_as_diagnostic(payload):
    fetch, _, _ = collector(payload)
    out = fetch(PLAN, raw_funding_only=True)
    assert out["funding_rows"] == [] and len(out["funding_observations"]) == 1
    assert out["checks"][0]["reason"] == "rate_unknown"
    assert out["funding_observations"][0]["payload"] == payload


def test_fetch_error_is_sanitized_without_retry_and_client_closes():
    fetch, trace, _ = collector({}, failure=RuntimeError("sensitive-looking message must not appear"))
    out = fetch(PLAN, raw_funding_only=True)
    assert out["funding_observations"] == []
    assert trace == [("fetch", "native:EXAMPLE"), "close"]
    assert out["checks"][0]["reason"] == "funding_raw_capture_failed:RuntimeError"
    assert "sensitive-looking" not in str(out)


@pytest.mark.parametrize("response_symbol, expected", [(None, None), ("different", False)])
def test_symbol_uncertainty_is_retained_not_certified(response_symbol, expected):
    fetch, _, _ = collector({"symbol": response_symbol, "fundingRate": 0.0001})
    inputs = fetch(PLAN, raw_funding_only=True)["funding_observations"][0]
    record = observation(**inputs)
    assert record["receipt"]["response_symbol_matches_request"] is expected
    assert record["normalization"]["eligible"] is False


@pytest.mark.parametrize("kwargs", [
    {"raw_funding_only": "yes"}, {"raw_funding_only": True},
    {"raw_funding_only": True, "raw_funding_max_rows": True, "raw_funding_max_bytes": 100},
    {"raw_funding_only": True, "raw_funding_max_rows": 1, "raw_funding_max_bytes": 0},
])
def test_bad_mode_or_missing_limits_refuses_before_fetch(tmp_path, kwargs):
    def refuse(*args, **kwargs):
        raise AssertionError("must not fetch")
    with pytest.raises(ValueError):
        service(PLAN, refuse, tmp_path / "unused.sqlite")(**kwargs)
    assert not (tmp_path / "unused.sqlite").exists()


def test_plan_limit_refuses_before_any_exchange_call(tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("must not fetch")
    with pytest.raises(ValueError, match="plan_row_budget"):
        service({"funding": PLAN["funding"] * 2}, refuse, tmp_path / "unused.sqlite")(
            raw_funding_only=True, raw_funding_max_rows=1, raw_funding_max_bytes=32768)
    assert not (tmp_path / "unused.sqlite").exists()


@pytest.mark.parametrize("plan", [PLAN, {"funding": []}])
def test_legacy_default_collector_result_is_identical(plan):
    current, current_trace, _ = collector({"fundingRate": 0.0001})
    old, old_trace, _ = collector({"fundingRate": 0.0001}, old=True)
    assert current(plan) == old(plan)
    assert current_trace == old_trace


def test_legacy_default_service_result_is_identical(tmp_path):
    class FakeStore:
        def __init__(self, **kwargs):
            pass
        def append_funding_rows(self, *args, **kwargs):
            return "same-snapshot"
        def latest_report_for_source(self, **kwargs):
            return {"funding": {"legacy": True}, "has_any_data": True}
    def fetch(plan):
        return {"funding_rows": [{"funding_rate": 0.0001}], "checks": []}
    current = service(PLAN, fetch, tmp_path / "unused.sqlite", store_class=FakeStore)
    old = service(PLAN, fetch, tmp_path / "unused.sqlite", old=True, store_class=FakeStore)
    assert current() == old()


@pytest.mark.parametrize("payload", [
    {"fundingRate": 0.0001}, {"nextFundingRate": "0.0001", "interval": "4h"},
    {"fundingRate": 0, "info": {"time": 1700000000000}},
])
def test_no_receipt_v1_results_match_frozen_decoder(payload):
    inputs = {"venue": "okx", "symbol": "EXAMPLE", "captured_at": "2026-10-29T00:00:00Z", "payload": payload}
    assert observation(**inputs) == frozen(**inputs)


def test_regressed_receipt_clock_is_retained_as_uncertainty():
    record = observation(venue="okx", symbol="EXAMPLE", captured_at="2026-10-29T00:00:00Z", payload={},
                         receipt={"request_started_at": "2026-10-29T00:00:01Z",
                                  "received_at": "2026-10-29T00:00:00Z",
                                  "requested_symbol": "EXAMPLE", "fetch_method": "fetch_funding_rate"})
    assert record["receipt"]["clock_ordered"] is False
    assert record["normalization"]["eligible"] is False


def test_receipt_schema_roundtrip_does_not_upgrade_old_rows(tmp_path):
    path = tmp_path / "versions.sqlite"
    store = storage.CryptoEdgeStoreSQLite(path=str(path))
    legacy = {"venue": "okx", "symbol": "EXAMPLE", "captured_at": "2026-10-29T00:00:00Z",
              "payload": {"fundingRate": 0.0001, "info": {"time": 1700000000000}}}
    store.append_raw_funding_observations([legacy], source="synthetic", max_rows=2, max_bytes=32768)
    fetch, _, _ = collector({"fundingRate": 0.0001})
    receipt = fetch(PLAN, raw_funding_only=True)["funding_observations"][0]
    store.append_raw_funding_observations([receipt], source="synthetic", max_rows=2, max_bytes=32768)
    records = store.recent_raw_funding_observations(source="synthetic", limit=2)["observations"]
    assert {r["observation"]["schema"] for r in records} == {1, 2}
    v1 = next(r["observation"] for r in records if r["observation"]["schema"] == 1)
    assert v1 == frozen(**legacy) and "receipt" not in v1


def test_rehashed_receipt_type_change_is_not_validated_as_exact_evidence(tmp_path):
    fetch, _, _ = collector({"fundingRate": 0.0001})
    record = observation(**fetch(PLAN, raw_funding_only=True)["funding_observations"][0])
    record["receipt"]["clock_ordered"] = 1
    path = tmp_path / "corrupt.sqlite"
    store = storage.CryptoEdgeStoreSQLite(path=str(path))
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO raw_funding_observations"
                     "(source,observation_key,capture_ts,payload_json) VALUES(?,?,?,?)",
                     ("synthetic", identity(record), record["captured_at"], encoded(record)))
    with pytest.raises(ValueError, match="stored_raw_funding_corrupt"):
        store.recent_raw_funding_observations(source="synthetic", limit=1)


@pytest.mark.parametrize("raw", [False, True])
def test_mixed_capture_contract_refuses_before_store_construction(tmp_path, raw):
    def fetch(*args, **kwargs):
        return {"funding_rows": [{}] if raw else [],
                "funding_observations": [] if raw else [{}]}
    path = tmp_path / "not-created.sqlite"
    kwargs = {"raw_funding_only": raw}
    if raw:
        kwargs.update(raw_funding_max_rows=1, raw_funding_max_bytes=32768)
    with pytest.raises(ValueError, match="mixed_funding_capture_contract"):
        service(PLAN, fetch, path)(**kwargs)
    assert not path.exists()


def test_reused_sdk_payload_does_not_mutate_an_earlier_receipt():
    fetch, _, ns = collector({})
    payload = {}
    numbers = count(1)
    class Reused:
        def fetch_funding_rate(self, symbol):
            payload["fundingRate"] = str(next(numbers))
            return payload
    ns["_open_public_exchange"] = lambda venue: Reused()
    plan = {"funding": [{"venue": "okx", "symbol": "ONE"}, {"venue": "okx", "symbol": "TWO"}]}
    records = fetch(plan, raw_funding_only=True)["funding_observations"]
    assert records[0]["payload"]["fundingRate"] == "1"
    assert records[1]["payload"]["fundingRate"] == "2"
