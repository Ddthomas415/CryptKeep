from __future__ import annotations

import math

import pytest

from storage.order_manager_store_sqlite import OrderManagerStoreSQLite


def _store(tmp_path):
    return OrderManagerStoreSQLite(tmp_path / "order_manager.sqlite")


@pytest.mark.parametrize(
    ("field", "qty", "price"),
    [
        ("qty", float("nan"), 100.0),
        ("price", 1.0, float("inf")),
    ],
)
def test_idem_set_rejects_nonfinite_numerics_before_mutation(tmp_path, field, qty, price):
    store = _store(tmp_path)

    with pytest.raises(ValueError, match=rf"invalid_order_manager_numeric:{field}:"):
        store.idem_set("idem-1", "coinbase", "BTC/USD", "buy", qty, price, "order-1")

    assert store.recent_idem(limit=10) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("qty", float("nan")),
        ("price", float("inf")),
        ("filled", -float("inf")),
        ("average", math.nan),
    ],
)
def test_upsert_order_snapshot_rejects_nonfinite_numerics_before_mutation(tmp_path, field, value):
    store = _store(tmp_path)
    snapshot = {
        "status": "open",
        "side": "buy",
        "qty": 1.0,
        "price": 100.0,
        "filled": 0.0,
        "average": 0.0,
    }
    snapshot[field] = value

    with pytest.raises(ValueError, match=rf"invalid_order_manager_numeric:{field}:"):
        store.upsert_order_snapshot("coinbase", "BTC/USD", "order-1", snapshot)

    assert store.recent_orders(limit=10) == []


def test_upsert_order_snapshot_preserves_missing_numeric_defaults(tmp_path):
    store = _store(tmp_path)

    store.upsert_order_snapshot(
        "coinbase",
        "BTC/USD",
        "order-1",
        {"status": "open", "side": "buy"},
    )

    rows = store.recent_orders(limit=10)
    assert len(rows) == 1
    assert rows[0]["qty"] == 0.0
    assert rows[0]["price"] == 0.0
    assert rows[0]["filled"] == 0.0
    assert rows[0]["average"] == 0.0
