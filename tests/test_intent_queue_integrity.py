from __future__ import annotations

import importlib


def _reload_queue(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import storage.intent_queue_sqlite as queue_mod

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    return queue_mod


def test_intent_queue_update_status_allows_submit_and_updates_mutable_fields(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.IntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-1",
            "created_ts": "2026-04-23T12:00:00Z",
            "ts": "2026-04-23T12:00:00Z",
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
            "linked_order_id": None,
        }
    )

    qdb.update_status(
        "intent-1",
        "submitted",
        last_error=None,
        client_order_id="paper_intent_intent-1",
        linked_order_id="paper-order-1",
    )

    row = qdb.get_intent("intent-1")
    assert row is not None
    assert row["status"] == "submitted"
    assert row["client_order_id"] == "paper_intent_intent-1"
    assert row["linked_order_id"] == "paper-order-1"


def test_intent_queue_update_status_blocks_invalid_backward_transition(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.IntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-2",
            "created_ts": "2026-04-23T12:00:00Z",
            "ts": "2026-04-23T12:00:00Z",
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
            "linked_order_id": None,
        }
    )
    qdb.update_status(
        "intent-2",
        "submitted",
        last_error=None,
        client_order_id="paper_intent_intent-2",
        linked_order_id="paper-order-2",
    )

    qdb.update_status(
        "intent-2",
        "queued",
        last_error="should_not_apply",
        client_order_id="bad-cid",
        linked_order_id="bad-order",
    )

    row = qdb.get_intent("intent-2")
    assert row is not None
    assert row["status"] == "submitted"
    assert row["last_error"] is None
    assert row["client_order_id"] == "paper_intent_intent-2"
    assert row["linked_order_id"] == "paper-order-2"


def test_intent_queue_update_status_blocks_terminal_overwrite(monkeypatch, tmp_path):
    queue_mod = _reload_queue(monkeypatch, tmp_path)
    qdb = queue_mod.IntentQueueSQLite()

    qdb.upsert_intent(
        {
            "intent_id": "intent-3",
            "created_ts": "2026-04-23T12:00:00Z",
            "ts": "2026-04-23T12:00:00Z",
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
            "linked_order_id": None,
        }
    )
    qdb.update_status(
        "intent-3",
        "submitted",
        client_order_id="paper_intent_intent-3",
        linked_order_id="paper-order-3",
    )
    qdb.update_status("intent-3", "filled", last_error=None)

    qdb.update_status("intent-3", "rejected", last_error="late_error")

    row = qdb.get_intent("intent-3")
    assert row is not None
    assert row["status"] == "filled"
    assert row["last_error"] is None
