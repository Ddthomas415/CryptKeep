import storage.live_intent_queue_sqlite as mod


def _queued_intent():
    return {
        "intent_id": "intent-claim-1",
        "created_ts": "2026-04-26T00:00:00Z",
        "ts": "2026-04-26T00:00:00Z",
        "source": "strategy",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 1.0,
        "limit_price": 100.0,
        "status": "queued",
        "last_error": None,
        "client_order_id": None,
        "exchange_order_id": None,
    }


def test_claim_next_queued_winner_takes_row(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db1 = mod.LiveIntentQueueSQLite()
    db2 = mod.LiveIntentQueueSQLite()
    db1.upsert_intent(_queued_intent())

    first = db1.claim_next_queued(limit=10)
    second = db2.claim_next_queued(limit=10)

    assert [row["intent_id"] for row in first] == ["intent-claim-1"]
    assert first[0]["status"] == "submitting"
    assert first[0]["client_order_id"] == "live_intent_intent-claim-1"
    assert second == []


def test_next_queued_remains_read_only_for_observability(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()
    db.upsert_intent(_queued_intent())

    first = db.next_queued(limit=10)
    second = db.next_queued(limit=10)

    assert [row["intent_id"] for row in first] == ["intent-claim-1"]
    assert [row["intent_id"] for row in second] == ["intent-claim-1"]
