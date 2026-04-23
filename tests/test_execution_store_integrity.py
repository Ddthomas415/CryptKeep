from __future__ import annotations

import sqlite3

from services.execution.intent_lifecycle import execution_store_transition_allowed
from storage.execution_store_sqlite import ExecutionStore


def _row_status_reason(path: str, intent_id: str) -> tuple[str, str | None]:
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT status, reason FROM intents WHERE intent_id=?",
            (intent_id,),
        ).fetchone()
    assert row is not None
    return str(row[0]), row[1]


def test_execution_store_transition_rules_are_shared_lifecycle_truth() -> None:
    assert execution_store_transition_allowed("pending", "submitted") is True
    assert execution_store_transition_allowed("submitted", "filled") is True
    assert execution_store_transition_allowed("filled", "pending") is False


def test_execution_store_blocks_status_regression_and_keeps_forward_progress(tmp_path):
    path = str(tmp_path / "execution.sqlite")
    store = ExecutionStore(path=path)
    store.upsert_intent(
        {
            "intent_id": "intent-1",
            "ts_ms": 1,
            "mode": "live",
            "exchange": "coinbase",
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "limit",
            "qty": 0.25,
            "limit_price": 100.0,
            "status": "pending",
        }
    )

    store.set_intent_status(intent_id="intent-1", status="submitted", reason="remote_id=ord-1")
    assert _row_status_reason(path, "intent-1") == ("submitted", "remote_id=ord-1")

    store.set_intent_status(intent_id="intent-1", status="filled", reason="remote_id=ord-1")
    assert _row_status_reason(path, "intent-1") == ("filled", "remote_id=ord-1")

    store.set_intent_status(intent_id="intent-1", status="pending", reason="should_not_regress")
    assert _row_status_reason(path, "intent-1") == ("filled", "remote_id=ord-1")

    store.set_intent_status(intent_id="intent-1", status="filled", reason="remote_id=ord-1:confirmed")
    assert _row_status_reason(path, "intent-1") == ("filled", "remote_id=ord-1:confirmed")


def test_execution_store_dedups_duplicate_trade_id_fills(tmp_path):
    path = str(tmp_path / "execution.sqlite")
    store = ExecutionStore(path=path)

    store.add_fill(
        intent_id="intent-1",
        ts_ms=1_700_000_000_000,
        price=100.0,
        qty=0.25,
        fee=0.01,
        fee_ccy="USD",
        meta={"trade_id": "trade-1"},
    )
    store.add_fill(
        intent_id="intent-1",
        ts_ms=1_700_000_000_001,
        price=100.0,
        qty=0.25,
        fee=0.01,
        fee_ccy="USD",
        meta={"trade_id": "trade-1"},
    )

    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT COUNT(*), MAX(trade_id) FROM fills WHERE intent_id=?",
            ("intent-1",),
        ).fetchone()

    assert row == (1, "trade-1")
    assert store.list_fill_trade_ids(intent_id="intent-1") == ["trade-1"]


def test_execution_store_adds_trade_id_column_and_unique_index_for_existing_db(tmp_path):
    path = str(tmp_path / "execution.sqlite")
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS intents(
              intent_id TEXT PRIMARY KEY,
              ts_ms INTEGER NOT NULL,
              mode TEXT NOT NULL,
              exchange TEXT NOT NULL,
              symbol TEXT NOT NULL,
              side TEXT NOT NULL,
              order_type TEXT NOT NULL,
              qty REAL NOT NULL,
              limit_price REAL,
              status TEXT NOT NULL,
              reason TEXT,
              meta_json TEXT
            );

            CREATE TABLE IF NOT EXISTS fills(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              intent_id TEXT NOT NULL,
              ts_ms INTEGER NOT NULL,
              price REAL NOT NULL,
              qty REAL NOT NULL,
              fee REAL NOT NULL,
              fee_ccy TEXT NOT NULL,
              meta_json TEXT
            );
            """
        )

    ExecutionStore(path=path)

    with sqlite3.connect(path) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(fills)").fetchall()}
        indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(fills)").fetchall()
        }

    assert "trade_id" in cols
    assert "idx_fills_intent_trade_id" in indexes
