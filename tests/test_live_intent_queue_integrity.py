from __future__ import annotations

import importlib

from services.execution.intent_lifecycle import live_queue_transition_allowed


def _reload_queue(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    return queue_mod


def test_live_intent_queue_upsert_preserves_creation_and_link_fields(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-1",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "market",
            "qty": 0.5,
            "limit_price": None,
            "status": "queued",
            "last_error": None,
            "client_order_id": "cid-1",
            "exchange_order_id": "ord-1",
        }
    )

    qdb.upsert_intent(
        {
            "intent_id": "intent-1",
            "created_ts": "2099-01-01T00:00:00Z",
            "ts": "2026-04-02T12:05:00Z",
            "source": "strategy_refresh",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "sell",
            "order_type": "limit",
            "qty": 1.25,
            "limit_price": 101.5,
            "status": "queued",
            "last_error": "should_not_replace",
            "client_order_id": None,
            "exchange_order_id": None,
        }
    )

    row = qdb.list_intents(limit=5)[0]
    assert row["intent_id"] == "intent-1"
    assert row["created_ts"] == "2026-04-02T12:00:00Z"
    assert row["client_order_id"] == "cid-1"
    assert row["exchange_order_id"] == "ord-1"
    assert row["last_error"] is None
    assert row["ts"] == "2026-04-02T12:05:00Z"
    assert row["source"] == "strategy_refresh"
    assert row["side"] == "sell"
    assert row["order_type"] == "limit"
    assert row["qty"] == 1.25
    assert row["limit_price"] == 101.5


def test_live_intent_queue_update_status_still_updates_mutable_fields(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-2",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
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
        }
    )

    qdb.update_status(
        "intent-2",
        "submitted",
        last_error=None,
        client_order_id="cid-2",
        exchange_order_id="ord-2",
    )

    row = qdb.list_intents(limit=5)[0]
    assert row["intent_id"] == "intent-2"
    assert row["status"] == "submitted"
    assert row["client_order_id"] == "cid-2"
    assert row["exchange_order_id"] == "ord-2"


def test_live_intent_queue_transition_rules_are_shared_lifecycle_truth() -> None:
    assert live_queue_transition_allowed("queued", "submitted") is True
    assert live_queue_transition_allowed("submitted", "filled") is True
    assert live_queue_transition_allowed("submitted", "queued") is False
    assert live_queue_transition_allowed("filled", "error") is False


def test_live_intent_queue_update_status_blocks_invalid_transition(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-3",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
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
        }
    )
    qdb.update_status("intent-3", "submitted", client_order_id="cid-3", exchange_order_id="ord-3")

    qdb.update_status(
        "intent-3",
        "queued",
        last_error="should_not_apply",
        client_order_id="bad-cid",
        exchange_order_id="bad-ord",
    )

    row = qdb.list_intents(limit=5)[0]
    assert row["status"] == "submitted"
    assert row["last_error"] is None
    assert row["client_order_id"] == "cid-3"
    assert row["exchange_order_id"] == "ord-3"


def test_live_intent_queue_update_status_blocks_terminal_overwrite(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.LiveIntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-4",
            "created_ts": "2026-04-02T12:00:00Z",
            "ts": "2026-04-02T12:00:00Z",
            "source": "strategy",
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
        }
    )
    qdb.update_status("intent-4", "submitted", client_order_id="cid-4", exchange_order_id="ord-4")
    qdb.update_status("intent-4", "filled", last_error=None)

    qdb.update_status("intent-4", "error", last_error="late_error")

    row = qdb.list_intents(limit=5)[0]
    assert row["status"] == "filled"
    assert row["last_error"] is None
