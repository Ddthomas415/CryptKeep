import storage.live_intent_queue_sqlite as mod


def _row():
    return {
        "intent_id": "i1",
        "created_ts": "2026-01-01T00:00:00Z",
        "ts": "2026-01-01T00:00:00Z",
        "source": "s",
        "strategy_id": "strat",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 1.0,
        "limit_price": 100.0,
        "status": "queued",
        "meta": {},
    }


def test_queued_can_transition_to_submit_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    db.upsert_intent(_row())

    assert db.update_status(
        "i1",
        "submit_unknown",
        last_error="TimeoutError:x",
        client_order_id="cid-1",
    )

    got = db.list_intents(limit=1)[0]
    assert got["status"] == "submit_unknown"
    assert got["client_order_id"] == "cid-1"
    assert got["last_error"] == "TimeoutError:x"


def test_submit_unknown_can_resolve_to_submitted(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    db.upsert_intent(_row())
    assert db.update_status("i1", "submit_unknown", client_order_id="cid-1")
    assert db.update_status("i1", "submitted", exchange_order_id="ex-1")

    got = db.list_intents(limit=1)[0]
    assert got["status"] == "submitted"
    assert got["exchange_order_id"] == "ex-1"


def test_submit_unknown_can_resolve_to_error(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    db.upsert_intent(_row())
    assert db.update_status("i1", "submit_unknown", client_order_id="cid-1")
    assert db.update_status("i1", "error", last_error="unresolved_submit_unknown")

    got = db.list_intents(limit=1)[0]
    assert got["status"] == "error"
    assert got["last_error"] == "unresolved_submit_unknown"
