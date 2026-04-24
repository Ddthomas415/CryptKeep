import storage.intent_queue_sqlite as paper_mod
import storage.live_intent_queue_sqlite as live_mod


def test_paper_queue_update_status_preserves_existing_ids_on_none(monkeypatch, tmp_path):
    db = tmp_path / "intent_queue.sqlite"
    monkeypatch.setattr(paper_mod, "DB_PATH", db)

    q = paper_mod.IntentQueueSQLite()
    q.upsert_intent({
        "intent_id": "i1",
        "created_ts": "2026-01-01T00:00:00+00:00",
        "ts": "2026-01-01T00:00:00+00:00",
        "source": "test",
        "strategy_id": None,
        "action": None,
        "venue": "paper",
        "symbol": "BTC/USDT",
        "side": "buy",
        "qty": 1.0,
        "limit_price": None,
        "order_type": "market",
        "status": "submitted",
        "last_error": None,
        "client_order_id": "coid-1",
        "linked_order_id": "oid-1",
        "meta": None,
    })

    q.update_status("i1", "rejected", last_error="boom")

    row = q.get_intent("i1")
    assert row is not None
    assert row["status"] == "rejected"
    assert row["client_order_id"] == "coid-1"
    assert row["linked_order_id"] == "oid-1"


def test_live_queue_update_status_preserves_existing_ids_on_none(monkeypatch, tmp_path):
    db = tmp_path / "live_intent_queue.sqlite"
    monkeypatch.setattr(live_mod, "DB_PATH", db)

    q = live_mod.LiveIntentQueueSQLite()
    q.upsert_intent({
        "intent_id": "i1",
        "created_ts": "2026-01-01T00:00:00+00:00",
        "ts": "2026-01-01T00:00:00+00:00",
        "source": "test",
        "strategy_id": None,
        "venue": "binance",
        "symbol": "BTC/USDT",
        "side": "buy",
        "order_type": "market",
        "qty": 1.0,
        "limit_price": None,
        "status": "submitted",
        "last_error": None,
        "client_order_id": "coid-1",
        "exchange_order_id": "oid-1",
        "meta": None,
    })

    q.update_status("i1", "rejected", last_error="boom")

    rows = q.list_intents(limit=10)
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "rejected"
    assert row["client_order_id"] == "coid-1"
    assert row["exchange_order_id"] == "oid-1"
