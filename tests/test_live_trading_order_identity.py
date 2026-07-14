import pytest

import storage.live_trading_sqlite as mod


def _order(**overrides):
    row = {
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
    }
    row.update(overrides)
    return row


def test_upsert_order_preserves_created_ts_when_order_status_updates(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_trading.sqlite")
    db = mod.LiveTradingSQLite()

    db.upsert_order(_order())
    db.upsert_order(_order(exchange_order_id="ex-1", status="submitted", last_error=None))

    row = db.list_orders(limit=10)[0]

    assert row["client_order_id"] == "cid-1"
    assert row["created_ts"] == "2026-01-01T00:00:00Z"
    assert row["exchange_order_id"] == "ex-1"
    assert row["status"] == "submitted"
    assert row["last_error"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("qty", float("nan")),
        ("limit_price", float("inf")),
    ],
)
def test_upsert_order_rejects_nonfinite_numeric_inputs_before_mutation(tmp_path, monkeypatch, field, value):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_trading.sqlite")
    db = mod.LiveTradingSQLite()
    row = _order(**{field: value})

    with pytest.raises(ValueError, match=f"invalid_live_trading_numeric:{field}:"):
        db.upsert_order(row)

    assert db.list_orders(limit=10) == []
