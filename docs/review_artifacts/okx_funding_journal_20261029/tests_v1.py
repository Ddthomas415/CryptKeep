import base64
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import hashlib
from pathlib import Path
import socket
import sqlite3
from threading import Barrier

import pytest

from services.analytics.funding_observations import encoded, identity, observation
from services.analytics.okx_funding_journal import (
    append_okx_funding_pairs, pair_journal_inputs, recent_okx_funding_quotes,
)
from storage import crypto_edge_store_sqlite as storage


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("external/default boundary forbidden")
    connect = sqlite3.connect
    def temporary(database, *args, **kwargs):
        assert Path(database).resolve().is_relative_to(tmp_path.resolve())
        return connect(database, *args, **kwargs)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(sqlite3, "connect", temporary)
    monkeypatch.setattr(storage, "ensure_dirs", refuse)


@pytest.fixture
def store(tmp_path):
    return storage.CryptoEdgeStoreSQLite(path=str(tmp_path / "journal.sqlite"))


@pytest.fixture
def pair():
    # A saved parsing fixture, not a fresh capture or market-data experiment.
    path = ROOT / "docs/review_artifacts/okx_funding_metadata_20261029/20261029T103617Z_2668220f5a85484580a593b0207494d4"
    manifest = json.loads((path / "MANIFEST.json").read_bytes())
    result = {"requested_inst_id": "BTC-USDT-SWAP"}
    for name in ("current", "history"):
        row = next(item for item in manifest["records"] if item["name"] == name)
        result[name + "_body"] = (path / row["body_file"]).read_bytes()
        result[name + "_receipt"] = row
    return result


def write(store, pairs, source="fixture", **budgets):
    return append_okx_funding_pairs(store, pairs, source=source,
                                   **({"max_rows": 10, "max_bytes": 131072} | budgets))


def read(store, source="fixture", limit=10):
    return recent_okx_funding_quotes(store, source=source, limit=limit)


def assert_unqualified(out):
    assert out["normalization_eligible"] is False
    assert out["strategy_eligible"] is False and out["execution_authority"] is False
    for row in out["quotes"]:
        policy = row["policy"]
        assert policy["strategy_eligible"] is False and policy["execution_authority"] is False
        assert policy["crowding_comparable"] is False and policy["annualized_pct"] is None


def test_promotions_are_identical_except_one_internal_import():
    assert (ROOT / "services/analytics/okx_funding_contract.py").read_bytes() == (
        ROOT / "scripts/research/synthetic_okx_funding_contract.py").read_bytes()
    promoted = (ROOT / "services/analytics/okx_funding_cash_cost.py").read_bytes()
    expected = (ROOT / "scripts/research/synthetic_okx_cash_cost.py").read_bytes().replace(
        b"from scripts.research.synthetic_okx_funding_contract import",
        b"from services.analytics.okx_funding_contract import")
    assert promoted == expected


def test_bytes_and_receipts_roundtrip_after_reopen_without_legacy_writes(store, pair):
    original = deepcopy(pair)
    assert write(store, [pair])["inserted"] == 1
    reopened = storage.CryptoEdgeStoreSQLite(path=store.path)
    record = reopened.recent_raw_funding_observations(source="fixture", limit=10)["observations"][0]["observation"]
    assert record["schema"] == 1 and record["funding_rate"] is None and record["interval_hours"] is None
    for name in ("current", "history"):
        response = record["raw_payload"]["responses"][name]
        assert base64.b64decode(response["body_base64"]) == pair[name + "_body"]
        assert response["receipt"] == pair[name + "_receipt"]
    out = read(reopened)
    assert out["quotes"][0]["policy"]["forecast_cash_cost"]["forecast_rate_per_8h"] == "0.0000436849743302"
    assert all(row["settled_rate_per_8h"] is None for row in out["quotes"][0]["policy"]["reported_settlements"])
    assert reopened.latest_funding_rows() == [] and pair == original
    assert_unqualified(out)


def test_idempotence_source_isolation_and_changed_evidence(store, pair):
    assert write(store, [pair, pair])["inserted"] == 1
    assert write(store, [pair])["duplicates"] == 1
    assert write(store, [pair], source="other")["inserted"] == 1
    changed = deepcopy(pair)
    changed["history_receipt"]["received_at"] = "2026-10-29T10:36:19Z"
    assert write(store, [changed])["inserted"] == 1
    assert read(store)["quotes"][0]["captured_at"] == "2026-10-29T10:36:19Z"
    assert len(read(store, "other")["quotes"]) == 1
    assert read(store, "missing")["quotes"] == []


def test_legacy_and_single_endpoint_rows_are_not_implicitly_upgraded(store, pair):
    store.append_funding_rows([{"symbol": "LEGACY", "venue": "okx", "funding_rate": 0.1}], source="fixture")
    legacy = deepcopy(store.latest_funding_rows())
    sdk = {"venue": "okx", "symbol": "BTC/USDT:USDT", "captured_at": "2026-10-29T00:00:02Z",
           "payload": {"fundingRate": "0.0002", "interval": "8h"}}
    store.append_raw_funding_observations([sdk], source="fixture", max_rows=1, max_bytes=32768)
    write(store, [pair])
    out = read(store)
    assert out["unrelated_observations"] == 1 and len(out["quotes"]) == 1
    assert store.latest_funding_rows() == legacy
    assert out["scan_exhaustive"] is False
    assert_unqualified(out)


@pytest.mark.parametrize("budgets", [{"max_rows": 0}, {"max_rows": True}, {"max_bytes": 0},
                                    {"max_bytes": True}, {"max_rows": 1}, {"max_bytes": 1}])
def test_budgets_refuse_before_new_store_connection(store, pair, budgets, monkeypatch):
    def refuse():
        raise AssertionError("validation must precede connection")
    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect", refuse)
        with pytest.raises(ValueError):
            write(store, [pair, pair], **budgets)
    assert read(store)["quotes"] == []


def test_bad_later_receipt_cannot_partially_write(store, pair, monkeypatch):
    bad = deepcopy(pair)
    bad["current_receipt"]["body_sha256"] = "bad"
    def refuse():
        raise AssertionError("prevalidation must not connect")
    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect", refuse)
        with pytest.raises(ValueError, match="receipt_integrity_failed"):
            write(store, [pair, bad])
    assert read(store)["quotes"] == []


def test_duplicate_bytes_count_towards_budget(store, pair):
    size = write(store, [pair])["encoded_value_bytes"]
    with pytest.raises(ValueError, match="byte_budget"):
        write(store, [pair, pair], max_bytes=size)
    assert len(read(store)["quotes"]) == 1


def test_sql_failure_rolls_back_entire_pair_batch(store, pair):
    second = deepcopy(pair)
    second["history_receipt"]["received_at"] = "2026-10-29T10:36:19Z"
    key = identity(observation(**pair_journal_inputs(**second)))
    with sqlite3.connect(store.path) as connection:
        connection.execute("CREATE TRIGGER pair_failure BEFORE INSERT ON raw_funding_observations "
                           "WHEN NEW.observation_key='" + key + "' "
                           "BEGIN SELECT RAISE(ABORT,'synthetic'); END")
    with pytest.raises(sqlite3.IntegrityError):
        write(store, [pair, second])
    assert read(store)["quotes"] == []


@pytest.mark.parametrize("fault", ["body", "receipt", "policy_pin", "derived", "base64"])
def test_invalid_rehashed_pair_is_retained_but_produces_no_quote(store, pair, fault):
    wrapped = pair_journal_inputs(**pair)
    payload = wrapped["payload"]
    if fault == "body":
        payload["responses"]["current"]["body_base64"] = base64.b64encode(b"{}").decode()
    elif fault == "receipt":
        payload["responses"]["current"]["receipt"]["body_sha256"] = "bad"
    elif fault == "policy_pin":
        payload["api_document_sha256"] = "other"
    elif fault == "derived":
        payload["forecast_cash_cost"] = {"calculation_available": True, "forecast_rate_per_8h": "9"}
    else:
        payload["responses"]["current"]["body_base64"] = "not-base64!"
    store.append_raw_funding_observations([wrapped], source="fixture", max_rows=1, max_bytes=131072)
    out = read(store)
    assert out["quotes"] == [] and len(out["diagnostics"]) == 1
    assert out["diagnostics"][0]["reason"] == "stored_okx_pair_unusable"
    assert len(store.recent_raw_funding_observations(source="fixture", limit=10)["observations"]) == 1
    assert_unqualified(out)


def test_rehashed_eligibility_forgery_refused_by_actual_store(store, pair):
    write(store, [pair])
    record = store.recent_raw_funding_observations(source="fixture", limit=10)["observations"][0]["observation"]
    record["normalization"]["eligible"] = True
    with sqlite3.connect(store.path) as connection:
        connection.execute("UPDATE raw_funding_observations SET observation_key=?,payload_json=?",
                           (identity(record), encoded(record)))
    with pytest.raises(ValueError, match="stored_raw_funding_corrupt"):
        read(store)


@pytest.mark.parametrize("source", [None, "", " padded ", True])
def test_explicit_source_required(store, pair, source):
    with pytest.raises(ValueError):
        write(store, [pair], source=source)
    with pytest.raises(ValueError):
        read(store, source=source)


@pytest.mark.parametrize("limit", [None, 0, True])
def test_explicit_reader_limit_required(store, limit):
    with pytest.raises(ValueError):
        read(store, limit=limit)


def test_limited_scan_does_not_claim_exhaustive_pair_coverage(store, pair):
    write(store, [pair])
    unrelated = {"venue": "okx", "symbol": "OTHER", "captured_at": "2026-10-29T11:00:00Z", "payload": {}}
    store.append_raw_funding_observations([unrelated], source="fixture", max_rows=1, max_bytes=32768)
    out = read(store, limit=1)
    assert out["scanned"] == 1 and out["quotes"] == [] and out["unrelated_observations"] == 1
    assert out["scan_exhaustive"] is False


def test_unknown_forecast_is_preserved_without_a_numeric_substitute(store, pair):
    payload = json.loads(pair["current_body"])
    payload["data"][0]["fundingRate"] = None
    pair["current_body"] = json.dumps(payload).encode()
    pair["current_receipt"]["body_bytes"] = len(pair["current_body"])
    pair["current_receipt"]["body_sha256"] = hashlib.sha256(pair["current_body"]).hexdigest()
    write(store, [pair])
    out = read(store)
    quote = out["quotes"][0]["policy"]["forecast_cash_cost"]
    assert quote["calculation_available"] is False and quote["forecast_rate_per_8h"] is None
    assert "forecast_rate_unknown" in quote["reasons"]
    assert out["diagnostics"] == []
    assert_unqualified(out)


def test_original_accepted_json_encoding_is_preserved_losslessly(store, pair):
    pair["current_body"] = pair["current_body"].decode().encode("utf-16")
    pair["current_receipt"]["body_bytes"] = len(pair["current_body"])
    pair["current_receipt"]["body_sha256"] = hashlib.sha256(pair["current_body"]).hexdigest()
    write(store, [pair])
    raw = store.recent_raw_funding_observations(source="fixture", limit=1)["observations"][0]["observation"]
    saved = raw["raw_payload"]["responses"]["current"]["body_base64"]
    assert base64.b64decode(saved) == pair["current_body"]
    assert len(read(store)["quotes"]) == 1


def test_read_report_mutation_cannot_change_journal_evidence(store, pair):
    write(store, [pair])
    first = read(store)
    first["quotes"][0]["policy"]["forecast_cash_cost"]["forecast_rate_per_8h"] = "9"
    second = read(store)
    assert second["quotes"][0]["policy"]["forecast_cash_cost"]["forecast_rate_per_8h"] == "0.0000436849743302"


def test_concurrent_identical_pairs_have_one_insert(store, pair):
    barrier = Barrier(2, timeout=3)
    def append():
        barrier.wait()
        return write(store, [pair])
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(append) for _ in range(2)]
        results = [future.result(timeout=5) for future in futures]
    assert sum(item["inserted"] for item in results) == 1
    assert len(read(store)["quotes"]) == 1
