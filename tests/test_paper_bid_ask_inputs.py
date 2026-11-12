"""Exercise read-only evaluation inputs against isolated synthetic ledger fills."""
from contextlib import closing
from datetime import timedelta
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from scripts import report_paper_run_diagnostics as report
from tests.test_hourly_candle_quality import market
from tests.test_paper_snapshot_quote import NOW, NOW_MS, guarded, quote, snapshot, submit

START = NOW.isoformat()
END = (NOW + timedelta(seconds=2)).isoformat()


def freeze(source, target):
    with closing(sqlite3.connect(source)) as original, closing(sqlite3.connect(target)) as archive:
        original.backup(archive)
        assert archive.execute("PRAGMA journal_mode=DELETE").fetchone() == ("delete",)
    return target


def test_export_uses_fill_receipt_and_preserves_ledger_prices(guarded, tmp_path):
    import storage.paper_trading_sqlite as ledger

    rig, path = guarded
    assert submit(rig.eng)["ok"]
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    rig.now[0] += timedelta(seconds=1)
    snapshot(path, quote(bid=109, ask=111, ts_ms=NOW_MS + 1000), root_ms=NOW_MS + 1000)
    assert submit(rig.eng, client="exit", side="sell")["ok"]
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    # An exclusive-end fill is never accidentally mixed into this window.
    rig.now[0] += timedelta(seconds=1)
    assert submit(rig.eng, client="outside")["ok"]
    assert rig.eng.evaluate_open_orders()["filled"] == 1
    archive = freeze(ledger.DB_PATH, tmp_path / "archive?input.sqlite")
    before = archive.read_bytes(), set(tmp_path.iterdir())
    result = report.bid_ask_inputs(archive, START, END)
    assert result["status"] == "complete_fill_inputs" and result["fee_bps_per_side"] == 50
    buy, sell = result["fills"]
    assert [buy["price"], sell["price"]] == [100, 110]
    assert buy["bid_ask_model"] == {"price": 101, "fee": 0.505,
                                    "cash_flow_quote": -101.505, "quote_currency": "USD"}
    assert sell["bid_ask_model"] == {"price": 109, "fee": 0.545,
                                     "cash_flow_quote": 108.455, "quote_currency": "USD"}
    assert (archive.read_bytes(), set(tmp_path.iterdir())) == before


@pytest.mark.parametrize("damage,reason", [
    ("missing", "missing_quote_receipt"), ("bad_json", "invalid_quote_receipt"),
    ("wrong_market", "wrong_market"), ("future", "future_quote"),
    ("corrupt_mid", "invalid_quote_receipt"), ("invalid_fee", "invalid_fill"),
    ("other_currency", "quote_currency_unverified"),
])
def test_incomplete_fill_evidence_is_not_replaced_with_midpoint(guarded, tmp_path, damage, reason):
    import storage.paper_trading_sqlite as ledger

    rig, _ = guarded
    assert submit(rig.eng)["ok"] and rig.eng.evaluate_open_orders()["filled"] == 1
    fill, = rig.eng.db.list_fills()
    key = "paper_fill_quote:" + fill["fill_id"]
    receipt = rig.eng.db.get_fill_quote_evidence(fill["fill_id"])
    with sqlite3.connect(ledger.DB_PATH) as con:
        if damage == "missing":
            con.execute("DELETE FROM paper_state WHERE k=?", (key,))
        elif damage == "invalid_fee":
            con.execute("UPDATE paper_fills SET fee=?", (float("inf"),))
        elif damage == "other_currency":
            con.execute("UPDATE paper_fills SET fee_currency='EUR'")
        else:
            if damage == "wrong_market":
                receipt["symbol"] = "BTC/USD"
            elif damage == "future":
                receipt["ts_ms"] += 1
            elif damage == "corrupt_mid":
                receipt["mid"] = 105
            con.execute("UPDATE paper_state SET v=? WHERE k=?",
                        ("invalid" if damage == "bad_json" else json.dumps(receipt), key))
    result = report.bid_ask_inputs(freeze(ledger.DB_PATH, tmp_path / "export.sqlite"), START, END)
    assert result["status"] == "INCOMPLETE"
    row, = result["fills"]
    assert row["reason"] == reason and row["bid_ask_model"] is None
    assert row["price"] == 100
    json.dumps(result, allow_nan=False)


def test_export_reports_empty_bad_timestamp_and_budget(guarded, tmp_path, monkeypatch):
    import storage.paper_trading_sqlite as ledger

    rig, _ = guarded
    empty = freeze(ledger.DB_PATH, tmp_path / "empty.sqlite")
    assert report.bid_ask_inputs(empty, START, END)["reason"] == "no_fills_in_window"
    assert submit(rig.eng)["ok"] and rig.eng.evaluate_open_orders()["filled"] == 1
    with sqlite3.connect(ledger.DB_PATH) as con:
        con.execute("UPDATE paper_fills SET ts='unknown'")
    archive = freeze(ledger.DB_PATH, tmp_path / "export.sqlite")
    assert report.bid_ask_inputs(archive, START, END)["reason"] == "unclassifiable_fill_timestamps"
    monkeypatch.setattr(report, "MAX_EVALUATION_FILLS", 0)
    assert report.bid_ask_inputs(archive, START, END)["reason"] == "account_fill_budget_exceeded"


def test_cli_fails_without_creating_nonexistent_explicit_database(tmp_path):
    db = tmp_path / "archive?missing.sqlite"
    command = [sys.executable, "-B", str(Path(report.__file__).resolve()), "--bid-ask-inputs",
               "--paper-db", str(db), "--start-utc", START, "--end-utc", END]
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode == 1
    assert json.loads(result.stdout)["reason"] == "account_database_unreadable"
    assert not db.exists()


@pytest.mark.parametrize("duplicate", ["quote", "fill", "order"])
def test_export_rejects_ambiguous_associations(guarded, tmp_path, duplicate):
    import storage.paper_trading_sqlite as ledger

    rig, _ = guarded
    assert submit(rig.eng)["ok"] and rig.eng.evaluate_open_orders()["filled"] == 1
    archive = freeze(ledger.DB_PATH, tmp_path / "export.sqlite")
    with closing(sqlite3.connect(archive)) as con, con:
        if duplicate == "quote":
            con.execute("CREATE TABLE state_copy AS SELECT * FROM paper_state")
            con.execute("DROP TABLE paper_state")
            con.execute("ALTER TABLE state_copy RENAME TO paper_state")
            con.execute("INSERT INTO paper_state SELECT * FROM paper_state WHERE k GLOB 'paper_fill_quote:*'")
        elif duplicate == "fill":
            con.execute("INSERT INTO paper_fills SELECT 'second', order_id, ts, price, qty, fee, fee_currency "
                        "FROM paper_fills")
            con.execute("INSERT INTO paper_state SELECT 'paper_fill_quote:second', v FROM paper_state "
                        "WHERE k GLOB 'paper_fill_quote:*'")
        else:
            con.execute("CREATE TABLE orders_copy AS SELECT * FROM paper_orders")
            con.execute("DROP TABLE paper_orders")
            con.execute("ALTER TABLE orders_copy RENAME TO paper_orders")
            con.execute("INSERT INTO paper_orders SELECT * FROM paper_orders")
    result = report.bid_ask_inputs(archive, START, END)
    assert result["status"] == "INCOMPLETE"
    assert result["reason"] == "ambiguous_fill_associations"
    assert result["fills"] == []


def test_export_refuses_checkpointed_wal_archive_without_creating_sidecars(guarded, tmp_path):
    import storage.paper_trading_sqlite as ledger

    rig, _ = guarded
    assert submit(rig.eng)["ok"] and rig.eng.evaluate_open_orders()["filled"] == 1
    archive = freeze(ledger.DB_PATH, tmp_path / "wal.sqlite")
    with closing(sqlite3.connect(archive)) as con:
        assert con.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        assert con.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] == 0
    before = archive.read_bytes(), set(tmp_path.iterdir())
    result = report.bid_ask_inputs(archive, START, END)
    assert (archive.read_bytes(), set(tmp_path.iterdir())) == before
    assert result["status"] == "INCOMPLETE"
    assert result["reason"] == "account_archive_requires_rollback_format"


def test_export_refuses_real_wal_frames_and_detached_main_without_writes(guarded, tmp_path):
    import storage.paper_trading_sqlite as ledger

    rig, _ = guarded
    assert submit(rig.eng)["ok"] and rig.eng.evaluate_open_orders()["filled"] == 1
    archive = freeze(ledger.DB_PATH, tmp_path / "source.sqlite")
    with closing(sqlite3.connect(archive)) as con:
        assert con.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        con.execute("PRAGMA wal_autocheckpoint=0")
        with con:
            con.execute("UPDATE paper_fills SET price=103")
        wal = Path(str(archive) + "-wal")
        assert wal.stat().st_size > 32
        detached = tmp_path / "detached.sqlite"
        detached.write_bytes(archive.read_bytes())
        before = {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
        assert report.bid_ask_inputs(archive, START, END)["reason"] == "account_archive_has_sidecars"
        assert report.bid_ask_inputs(detached, START, END)["reason"] == "account_archive_requires_rollback_format"
        assert {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()} == before


def test_export_rejects_rollback_journal_and_source_identity_change(guarded, tmp_path, monkeypatch):
    import storage.paper_trading_sqlite as ledger

    rig, _ = guarded
    assert submit(rig.eng)["ok"] and rig.eng.evaluate_open_orders()["filled"] == 1
    archive = freeze(ledger.DB_PATH, tmp_path / "export.sqlite")
    journal = Path(str(archive) + "-journal")
    journal.write_bytes(b"sentinel")
    assert report.bid_ask_inputs(archive, START, END)["reason"] == "account_archive_has_sidecars"
    assert journal.read_bytes() == b"sentinel"
    journal.unlink()
    identity = report._standalone_archive_identity
    first = identity(archive)
    observations = iter((first, ((0,), None)))
    monkeypatch.setattr(report, "_standalone_archive_identity", lambda _path: next(observations))
    result = report.bid_ask_inputs(archive, START, END)
    assert result["reason"] == "account_archive_changed" and result["fills"] == []
