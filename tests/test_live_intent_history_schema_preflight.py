from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "check_live_intent_history_schema.py"


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {"PATH": "/usr/bin:/bin", "CBP_STATE_DIR": str(tmp_path / "state")}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(REPO),
        env=env,
    )


def _db_path(tmp_path: Path) -> Path:
    return tmp_path / "state" / "data" / "live_intent_queue.sqlite"


def test_read_only_check_reports_missing_without_creating_db(tmp_path):
    out = _run(tmp_path, "--json")

    assert out.returncode == 1, out.stdout + out.stderr
    report = json.loads(out.stdout)
    assert report["ok"] is False
    assert report["status"] == "schema_uninitialized"
    assert report["reason"] == "live_intent_queue_db_missing"
    assert report["initialized"] is False
    assert report["db_exists"] is False
    assert not _db_path(tmp_path).exists()


def test_init_creates_live_intent_history_schema(tmp_path):
    out = _run(tmp_path, "--init", "--json")

    assert out.returncode == 0, out.stdout + out.stderr
    report = json.loads(out.stdout)
    assert report["ok"] is True
    assert report["status"] == "ready"
    assert report["reason"] == "live_trade_intent_events_ready"
    assert report["initialized"] is True
    assert report["event_history_table_exists"] is True
    assert report["missing_event_columns"] == []
    assert "event_id" in report["event_columns"]
    assert "post_status" in report["event_columns"]


def test_legacy_store_is_reported_missing_until_explicit_init(tmp_path):
    db = _db_path(tmp_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    try:
        con.execute(
            "CREATE TABLE live_trade_intents ("
            "intent_id TEXT PRIMARY KEY, created_ts TEXT NOT NULL, ts TEXT NOT NULL, "
            "source TEXT NOT NULL, strategy_id TEXT, venue TEXT NOT NULL, "
            "symbol TEXT NOT NULL, side TEXT NOT NULL, order_type TEXT NOT NULL, "
            "qty REAL NOT NULL, limit_price REAL, status TEXT NOT NULL, "
            "last_error TEXT, client_order_id TEXT, exchange_order_id TEXT, "
            "meta TEXT, updated_ts TEXT NOT NULL)"
        )
        con.commit()
    finally:
        con.close()

    read_only = _run(tmp_path, "--json")
    assert read_only.returncode == 1, read_only.stdout + read_only.stderr
    read_only_report = json.loads(read_only.stdout)
    assert read_only_report["db_exists"] is True
    assert read_only_report["event_history_table_exists"] is False
    assert read_only_report["reason"] == "live_trade_intent_events_missing"

    initialized = _run(tmp_path, "--init", "--json")
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    initialized_report = json.loads(initialized.stdout)
    assert initialized_report["ok"] is True
    assert initialized_report["event_history_table_exists"] is True
