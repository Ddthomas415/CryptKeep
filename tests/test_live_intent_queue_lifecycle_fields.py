import storage.live_intent_queue_sqlite as mod


def _row(**overrides):
    row = {
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
        "meta": {"v": 1},
    }
    row.update(overrides)
    return row


def test_live_upsert_preserves_lifecycle_fields_after_submit(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    db.upsert_intent(_row())
    assert db.update_status(
        "i1",
        "submitted",
        client_order_id="cid-1",
        exchange_order_id="ex-1",
    )

    db.upsert_intent(
        _row(
            status="queued",
            client_order_id="cid-overwrite",
            exchange_order_id="ex-overwrite",
            qty=2.0,
        )
    )

    got = db.list_intents(limit=1)[0]
    assert got["status"] == "submitted"
    assert got["client_order_id"] == "cid-1"
    assert got["exchange_order_id"] == "ex-1"
    assert got["qty"] == 1.0


def test_live_upsert_does_not_modify_terminal_row(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    db.upsert_intent(_row())
    assert db.update_status("i1", "rejected", last_error="x")

    db.upsert_intent(_row(status="queued", qty=9.0, meta={"v": 2}))

    got = db.list_intents(limit=1)[0]
    assert got["status"] == "rejected"
    assert got["last_error"] == "x"
    assert got["qty"] == 1.0
    assert got["meta"] == {"v": 1}
