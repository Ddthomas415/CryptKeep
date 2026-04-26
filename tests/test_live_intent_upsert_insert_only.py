import storage.live_intent_queue_sqlite as mod


def _row(**overrides):
    row = {
        "intent_id": "i1",
        "created_ts": "2026-01-01T00:00:00Z",
        "ts": "2026-01-01T00:00:00Z",
        "source": "source-a",
        "strategy_id": "strategy-a",
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


def test_upsert_existing_intent_is_insert_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_intent_queue.sqlite")
    db = mod.LiveIntentQueueSQLite()

    db.upsert_intent(_row())

    db.upsert_intent(
        _row(
            ts="2026-01-01T00:01:00Z",
            source="source-b",
            strategy_id="strategy-b",
            symbol="ETH/USD",
            side="sell",
            qty=9.0,
            limit_price=200.0,
            status="rejected",
            meta={"v": 2},
        )
    )

    got = db.list_intents(limit=1)[0]
    assert got["ts"] == "2026-01-01T00:00:00Z"
    assert got["source"] == "source-a"
    assert got["strategy_id"] == "strategy-a"
    assert got["symbol"] == "BTC/USD"
    assert got["side"] == "buy"
    assert got["qty"] == 1.0
    assert got["limit_price"] == 100.0
    assert got["status"] == "queued"
    assert got["meta"] == {"v": 1}
