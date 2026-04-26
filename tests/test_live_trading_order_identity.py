import storage.live_trading_sqlite as mod


def test_upsert_order_preserves_created_ts_when_order_status_updates(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_trading.sqlite")
    db = mod.LiveTradingSQLite()

    db.upsert_order({
        "client_order_id": "cid-1",
        "created_ts": "2026-01-01T00:00:00Z",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 1.0,
        "limit_price": 100.0,
        "exchange_order_id": None,
        "status": "submit_unknown",
        "last_error": "original_error",
    })
    db.upsert_order({
        "client_order_id": "cid-1",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 1.0,
        "limit_price": 100.0,
        "exchange_order_id": "ex-1",
        "status": "submitted",
        "last_error": None,
    })

    row = db.list_orders(limit=10)[0]

    assert row["client_order_id"] == "cid-1"
    assert row["created_ts"] == "2026-01-01T00:00:00Z"
    assert row["exchange_order_id"] == "ex-1"
    assert row["status"] == "submitted"
    assert row["last_error"] is None
