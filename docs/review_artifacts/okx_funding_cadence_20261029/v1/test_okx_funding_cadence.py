"""Offline source-cadence checks, not funding qualification or market research."""

import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import subprocess

import pytest

from services.analytics import edge_cadence as ec
from services.analytics.funding_observations import encoded, identity, observation
from services.analytics.okx_funding_journal import pair_journal_inputs
from storage import crypto_edge_store_sqlite as storage

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = datetime(2026, 10, 29, 18, 20, 57, 504633, tzinfo=timezone.utc)
NOW = CAPTURE + timedelta(seconds=1)
BTC = "BTC-USDT-SWAP"
ETH = "ETH-USDT-SWAP"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    connect = sqlite3.connect
    def scoped(database, *args, **kwargs):
        path = str(database).removeprefix("file:").split("?", 1)[0]
        assert Path(path).resolve().is_relative_to(tmp_path.resolve())
        return connect(database, *args, **kwargs)
    def refuse(*args, **kwargs):
        raise AssertionError("network/process/default state forbidden")
    monkeypatch.setattr(sqlite3, "connect", scoped)
    monkeypatch.setattr(storage, "ensure_dirs", refuse)
    monkeypatch.setattr(storage.CryptoEdgeStoreSQLite, "__init__", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)


@pytest.fixture
def record():
    path = ROOT / "docs/review_artifacts/okx_funding_pilot_20261029/20261029T182056Z_5544cd086ad64e1f8787f2e44546edc3/READBACK.json"
    return json.loads(path.read_bytes())["raw"]["observations"][0]["observation"]


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "cadence.sqlite"
    with sqlite3.connect(path) as conn:
        conn.executescript(storage.DDL)
        for table, fields, values in (
            ("open_interest_snapshots", "open_interest,price_change_pct", (1, 0)),
            ("basis_snapshots", "spot_px,perp_px,days_to_expiry", (1, 1, 7)),
        ):
            columns = "snapshot_id,capture_ts,source,symbol,venue,payload_json," + fields
            data = ("synthetic", CAPTURE.isoformat(), "fixture", BTC, "okx", "{}") + values
            conn.execute(f"INSERT INTO {table}({columns}) VALUES({','.join('?' for _ in data)})", data)
    return path


def put(db, record, *, source="fixture", payload=None, key=None, capture=None):
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO raw_funding_observations(source,observation_key,capture_ts,payload_json) VALUES(?,?,?,?)",
                     (source, key or identity(record), capture or record["captured_at"],
                      encoded(record) if payload is None else payload))


def other_record(record, inst=ETH, delay_seconds=0):
    pair = {"requested_inst_id": inst}
    for name, response in record["raw_payload"]["responses"].items():
        body = json.loads(base64.b64decode(response["body_base64"]))
        for row in body["data"]:
            row["instId"] = inst
        body = json.dumps(body).encode()
        receipt = deepcopy(response["receipt"])
        for field in ("request_started_at", "received_at"):
            receipt[field] = (datetime.fromisoformat(receipt[field]) + timedelta(seconds=delay_seconds)).isoformat()
        receipt.update(url=receipt["url"].replace(BTC, inst), body_bytes=len(body),
                       body_sha256=hashlib.sha256(body).hexdigest())
        pair[name + "_body"], pair[name + "_receipt"] = body, receipt
    return observation(**pair_journal_inputs(**pair))


def check(db, **kwargs):
    return ec.check_edge_cadence(store_path=str(db), now=NOW, paired_funding_source="fixture",
                                paired_funding_inst_ids=[BTC], **kwargs)


def test_valid_raw_pair_repairs_reproduced_gap_without_writes(db, record):
    put(db, record)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    assert ec.check_edge_cadence(store_path=str(db), now=NOW)["missing"] == ["funding"]
    out = check(db)
    assert out["ok"] is True and not out["missing"]
    assert out["paired_funding"]["lane"] == "validated_okx_pair_capture"
    assert out["paired_funding"]["instruments"][0]["status"] == "validated_capture"
    assert all(out["paired_funding"][key] is False for key in
               ("strategy_eligible", "normalization_eligible", "execution_authority"))
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM funding_snapshots").fetchone()[0] == 0


def test_exact_source_and_native_identity(db, record):
    put(db, record, source="another")
    put(db, other_record(record))
    assert check(db)["missing"] == ["funding"]
    put(db, record)
    assert check(db)["ok"] is True


def test_every_required_instrument_must_have_a_pair(db, record):
    put(db, record)
    args = dict(store_path=str(db), now=NOW, paired_funding_source="fixture", paired_funding_inst_ids=[BTC, ETH])
    assert ec.check_edge_cadence(**args)["ok"] is False
    put(db, other_record(record))
    assert ec.check_edge_cadence(**args)["ok"] is True


def test_latest_attempt_does_not_fall_back_to_previous_success(db, record):
    put(db, record)
    attempt = observation(venue="okx", symbol=BTC, captured_at=NOW.isoformat(),
                          payload={"contract": "okx_public_pair_attempt_v1", "reason": "failed"})
    put(db, attempt)
    out = check(db)
    assert out["ok"] is False and out["missing"] == ["funding"]
    assert out["paired_funding"]["instruments"][0]["status"] == "not_a_successful_pair"


@pytest.mark.parametrize("change", ["key", "body", "index", "naive_index", "wrapper", "interval"])
def test_tampered_pair_never_satisfies_cadence(db, record, change):
    options = {}
    if change == "key":
        options["key"] = "wrong"
    elif change == "body":
        record["raw_payload"]["responses"]["current"]["body_base64"] = "!invalid!"
    elif change == "index":
        options["capture"] = NOW.isoformat()
    elif change == "naive_index":
        options["capture"] = CAPTURE.replace(tzinfo=None).isoformat()
    elif change == "interval":
        record["interval_hours"] = 8
    else:
        record["venue"] = "other"
    put(db, record, **options)
    assert check(db)["ok"] is False


@pytest.mark.parametrize("payload", ["{", "[]", '{"symbol":"BTC-USDT-SWAP","symbol":"ETH-USDT-SWAP"}',
                                    '{"symbol":"BTC-USDT-SWAP","x":1e999}', '[' * 2000 + '0' + ']' * 2000])
def test_malformed_overflow_duplicate_deep_rows_fail_closed(db, record, payload):
    put(db, record, payload=payload)
    out = check(db)
    assert out["ok"] is False and "funding" in out["missing"]
    assert out["paired_funding"]["diagnostics"] == ["unusable_raw_evidence"]


def test_future_capture_cannot_hide_behind_an_older_other_instrument(db, record):
    put(db, record)
    put(db, other_record(record, delay_seconds=2))
    out = ec.check_edge_cadence(store_path=str(db), now=NOW,
                                paired_funding_source="fixture", paired_funding_inst_ids=[BTC, ETH])
    assert out["ok"] is False and "funding" in out["missing"]
    assert [row["status"] for row in out["paired_funding"]["instruments"]] == ["validated_capture", "capture_in_future"]


def test_stale_pair_uses_existing_threshold(db, record):
    put(db, record)
    out = ec.check_edge_cadence(store_path=str(db), now=CAPTURE + timedelta(hours=13),
                                paired_funding_source="fixture", paired_funding_inst_ids=[BTC])
    assert "funding" in out["stale"] and out["ok"] is False


def test_missing_database_and_table_do_not_initialize(tmp_path, db):
    missing = tmp_path / "absent.sqlite"
    assert check(missing)["missing"] == ["funding", "open_interest", "basis"]
    assert not missing.exists()
    with sqlite3.connect(db) as conn:
        conn.execute("DROP TABLE raw_funding_observations")
    assert check(db)["missing"] == ["funding"]


def test_fresh_legacy_row_cannot_substitute_for_a_required_pair(db):
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO funding_snapshots(snapshot_id,capture_ts,source,symbol,venue,funding_rate,interval_hours,payload_json) VALUES(?,?,?,?,?,?,?,?)",
                     ("fixture", CAPTURE.isoformat(), "fixture", BTC, "okx", 0.001, 8, "{}"))
    assert ec.check_edge_cadence(store_path=str(db), now=NOW)["ok"] is True
    assert check(db)["missing"] == ["funding"]


def test_scan_limit_does_not_claim_unseen_identity_is_present(db, record):
    put(db, record)
    put(db, other_record(record))
    out = check(db, paired_funding_scan_limit=1)
    assert out["ok"] is False
    assert out["paired_funding"]["scan_exhaustive"] is False
    assert check(db, paired_funding_scan_limit=2)["ok"] is True


def test_oversized_raw_row_is_not_loaded_as_valid(db, record):
    put(db, record, payload='"' + "x" * 4194304 + '"')
    out = check(db)
    assert out["ok"] is False
    assert out["paired_funding"]["diagnostics"] == ["raw_evidence_byte_budget_exceeded"]


def test_total_byte_budget_bounds_unrelated_rows(db, record):
    # Each row fits individually; the third exceeds the aggregate decoding cap.
    for number in range(3):
        put(db, record, key=str(number), payload=json.dumps({"symbol": "UNRELATED", "padding": "x" * 3000000}))
    out = check(db)
    assert out["ok"] is False
    assert out["paired_funding"]["scanned"] == 3
    assert out["paired_funding"]["diagnostics"] == ["raw_evidence_byte_budget_exceeded"]


def test_25_distinct_instruments_have_no_single_symbol_shortcut(db, record):
    ids = [f"COIN{number}-USDT-SWAP" for number in range(25)]
    for inst in ids:
        put(db, other_record(record, inst))
    out = ec.check_edge_cadence(store_path=str(db), now=NOW, paired_funding_source="fixture",
                                paired_funding_inst_ids=ids)
    assert out["ok"] is True
    assert len(out["paired_funding"]["instruments"]) == 25


def test_recent_valid_row_wins_over_older_failure_but_not_other_way_round(db, record):
    attempt = observation(venue="okx", symbol=BTC, captured_at=CAPTURE.isoformat(), payload={"contract": "attempt"})
    put(db, attempt)
    put(db, record)
    assert check(db)["ok"] is True


@pytest.mark.parametrize("source,ids,limit", [(None, [BTC], 100), ("fixture", None, 100),
    (" fixture", [BTC], 100), ("fixture", [], 100), ("fixture", [BTC, BTC], 100),
    ("fixture", ["btc-usd"], 100), ("fixture", [BTC], True), ("fixture", [BTC], 0),
    ("fixture", [BTC], 1001)])
def test_invalid_scope_refuses_before_connect(monkeypatch, tmp_path, source, ids, limit):
    def refuse(*args, **kwargs):
        raise AssertionError("invalid configuration must not connect")
    monkeypatch.setattr(sqlite3, "connect", refuse)
    out = ec.check_edge_cadence(store_path=str(tmp_path / "missing.sqlite"),
        paired_funding_source=source, paired_funding_inst_ids=ids, paired_funding_scan_limit=limit)
    assert out["ok"] is False and out["store_error"] == "ValueError"


def test_cli_routes_exact_scope_and_preserves_exit_codes(monkeypatch, capsys, db, record):
    import scripts.check_edge_cadence as cli
    put(db, record)
    real = ec.check_edge_cadence
    def fixed(**kwargs):
        return real(**kwargs, now=NOW)
    monkeypatch.setattr(cli, "check_edge_cadence", fixed)
    args = ["--store-path", str(db), "--json", "--paired-funding-source", "fixture",
            "--paired-funding-inst-id", BTC]
    assert cli.main(args) == 0
    assert json.loads(capsys.readouterr().out)["paired_funding"]["source"] == "fixture"
    assert cli.main(args + ["--paired-funding-inst-id", ETH]) == 2
    capsys.readouterr()
    assert cli.main(args + ["--paired-funding-scan-limit", "0"]) == 2


def test_cli_rejects_orphan_scan_limit():
    import scripts.check_edge_cadence as cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--paired-funding-scan-limit", "2"])
    assert exc.value.code == 2


def test_legacy_future_time_is_not_clamped_to_fresh():
    out = ec.evaluate_cadence({"funding_meta": {"capture_ts": (NOW + timedelta(seconds=1)).isoformat()}}, now=NOW)
    row = next(item for item in out["families"] if item["family"] == "funding")
    assert row["status"] == "missing" and row["reason"] == "capture_in_future"
