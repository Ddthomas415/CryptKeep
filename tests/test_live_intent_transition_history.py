from __future__ import annotations

import importlib
import sqlite3


def _reload_queue(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    return queue_mod


def _row(**overrides):
    row = {
        "intent_id": "intent-history-1",
        "created_ts": "2026-04-02T12:00:00Z",
        "ts": "2026-04-02T12:00:00Z",
        "source": "strategy",
        "strategy_id": "ema_cross",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "market",
        "qty": 0.5,
        "limit_price": None,
        "status": "queued",
        "last_error": None,
        "client_order_id": None,
        "exchange_order_id": None,
        "meta": {"request_id": "r1"},
    }
    row.update(overrides)
    return row


def test_live_intent_events_record_insert_claim_and_status_transition(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(_row())
    claimed = qdb.claim_next_queued(limit=5)
    assert [row["intent_id"] for row in claimed] == ["intent-history-1"]
    assert qdb.update_status(
        "intent-history-1",
        "submitted",
        client_order_id="cid-1",
        exchange_order_id="ex-1",
    )

    events = qdb.list_intent_events(intent_id="intent-history-1")
    assert [event["action"] for event in events] == [
        "insert",
        "claim_next_queued",
        "update_status",
    ]
    assert [(event["pre_status"], event["post_status"]) for event in events] == [
        (None, "queued"),
        ("queued", "submitting"),
        ("submitting", "submitted"),
    ]
    assert events[0]["actor"] == "strategy"
    assert events[0]["reason"] == "upsert_intent_insert"
    assert events[0]["source"] == "strategy"
    assert events[0]["meta"]["insert_only"] is True
    assert events[1]["actor"] == "intent_consumer"
    assert events[1]["client_order_id"].startswith("live_intent_")
    assert events[2]["actor"] == "queue_status_writer"
    assert events[2]["client_order_id"] == "cid-1"
    assert events[2]["exchange_order_id"] == "ex-1"


def test_live_intent_events_do_not_record_noop_duplicate_or_invalid_transition(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(_row(intent_id="intent-history-2"))
    qdb.upsert_intent(_row(intent_id="intent-history-2", status="queued", qty=9.0))
    assert len(qdb.list_intent_events(intent_id="intent-history-2")) == 1

    assert qdb.update_status("intent-history-2", "submitted", client_order_id="cid-2")
    assert qdb.update_status("intent-history-2", "queued", last_error="bad_backward") is False
    events = qdb.list_intent_events(intent_id="intent-history-2")
    assert [event["post_status"] for event in events] == ["queued", "submitted"]
    assert all(event["last_error"] != "bad_backward" for event in events)


def test_live_intent_events_do_not_record_terminal_overwrite_attempt(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(_row(intent_id="intent-history-3"))
    assert qdb.update_status("intent-history-3", "submitted", client_order_id="cid-3")
    assert qdb.update_status("intent-history-3", "filled")
    assert qdb.update_status("intent-history-3", "rejected", last_error="late") is False

    events = qdb.list_intent_events(intent_id="intent-history-3")
    assert [event["post_status"] for event in events] == ["queued", "submitted", "filled"]
    assert events[-1]["pre_status"] == "submitted"
    assert all(event["last_error"] != "late" for event in events)


def test_live_intent_events_schema_created_for_existing_database(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    db_path = queue_mod.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE live_consumer_state (k TEXT PRIMARY KEY, v TEXT NOT NULL)")
    con.commit()
    con.close()

    qdb = queue_mod.LiveIntentQueueSQLite()
    qdb.upsert_intent(_row(intent_id="intent-history-4"))

    events = qdb.list_intent_events(intent_id="intent-history-4")
    assert len(events) == 1
    assert events[0]["post_status"] == "queued"
