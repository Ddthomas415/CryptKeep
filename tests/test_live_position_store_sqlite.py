import math
import sqlite3
from pathlib import Path

import pytest

from storage.live_position_store_sqlite import (
    LivePositionAccountingError,
    LivePositionStore,
)


def _row_count(db: str, table: str) -> int:
    con = sqlite3.connect(db)
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        con.close()


def test_live_position_store_computes_realized_pnl(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    s = LivePositionStore(db)

    buy = s.apply_fill(
        venue="coinbase",
        symbol="BTC/USD",
        fill_id="buy-1",
        side="buy",
        qty=0.01,
        price=60000.0,
    )
    assert buy["ok"] is True
    assert buy["realized_pnl_usd"] == 0.0

    sell = s.apply_fill(
        venue="coinbase",
        symbol="BTC/USD",
        fill_id="sell-1",
        side="sell",
        qty=0.01,
        price=58000.0,
    )
    assert sell["ok"] is True
    assert sell["realized_pnl_usd"] == pytest.approx(-20.0)
    assert sell["new_qty"] == pytest.approx(0.0)
    assert sell["new_avg_price"] == pytest.approx(0.0)


def test_live_position_store_is_idempotent_by_fill_id(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    s = LivePositionStore(db)

    first = s.apply_fill(
        venue="coinbase",
        symbol="BTC/USD",
        fill_id="dup-buy",
        side="buy",
        qty=0.01,
        price=60000.0,
    )
    second = s.apply_fill(
        venue="coinbase",
        symbol="BTC/USD",
        fill_id="dup-buy",
        side="buy",
        qty=0.01,
        price=60000.0,
    )

    pos = s.get_position("coinbase", "BTC/USD")

    assert first["idempotent"] is False
    assert second["idempotent"] is True
    assert pos["qty"] == pytest.approx(0.01)
    assert pos["avg_price"] == pytest.approx(60000.0)


def test_live_position_store_partial_sell_keeps_avg_price(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    s = LivePositionStore(db)

    s.apply_fill(
        venue="coinbase",
        symbol="BTC/USD",
        fill_id="buy-1",
        side="buy",
        qty=0.01,
        price=60000.0,
    )

    sell = s.apply_fill(
        venue="coinbase",
        symbol="BTC/USD",
        fill_id="sell-half",
        side="sell",
        qty=0.005,
        price=62000.0,
    )

    pos = s.get_position("coinbase", "BTC/USD")

    assert sell["realized_pnl_usd"] == pytest.approx(10.0)
    assert pos["qty"] == pytest.approx(0.005)
    assert pos["avg_price"] == pytest.approx(60000.0)


def test_live_position_store_sell_without_position_fails_closed(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    s = LivePositionStore(db)

    with pytest.raises(LivePositionAccountingError):
        s.apply_fill(
            venue="coinbase",
            symbol="BTC/USD",
            fill_id="bad-sell",
            side="sell",
            qty=0.01,
            price=58000.0,
        )


def test_live_position_store_oversell_fails_closed(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    s = LivePositionStore(db)

    s.apply_fill(
        venue="coinbase",
        symbol="BTC/USD",
        fill_id="buy-1",
        side="buy",
        qty=0.01,
        price=60000.0,
    )

    with pytest.raises(LivePositionAccountingError):
        s.apply_fill(
            venue="coinbase",
            symbol="BTC/USD",
            fill_id="oversell",
            side="sell",
            qty=0.02,
            price=61000.0,
        )


def test_live_position_store_reconcile_hook_reports_drift(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    s = LivePositionStore(db)

    s.apply_fill(
        venue="coinbase",
        symbol="BTC/USD",
        fill_id="buy-1",
        side="buy",
        qty=0.01,
        price=60000.0,
    )

    ok = s.reconcile_to_exchange(
        venue="coinbase",
        symbol="BTC/USD",
        exchange_qty=0.01,
    )
    drift = s.reconcile_to_exchange(
        venue="coinbase",
        symbol="BTC/USD",
        exchange_qty=0.02,
    )

    assert ok["ok"] is True
    assert drift["ok"] is False
    assert drift["drift"] == pytest.approx(0.01)


@pytest.mark.parametrize(
    ("field", "qty", "price"),
    [
        ("qty", float("nan"), 60000.0),
        ("price", 0.01, float("inf")),
    ],
)
def test_live_position_store_rejects_nonfinite_fill_numerics_before_mutation(tmp_path, field, qty, price):
    db = str(tmp_path / "execution.sqlite")
    s = LivePositionStore(db)

    with pytest.raises(LivePositionAccountingError, match=rf"invalid_live_position_numeric:{field}:"):
        s.apply_fill(
            venue="coinbase",
            symbol="BTC/USD",
            fill_id="bad-fill",
            side="buy",
            qty=qty,
            price=price,
        )

    assert s.get_position("coinbase", "BTC/USD") == {"qty": 0.0, "avg_price": 0.0}
    assert _row_count(db, "live_positions") == 0
    assert _row_count(db, "live_position_fills") == 0


@pytest.mark.parametrize(
    ("field", "exchange_qty", "tolerance"),
    [
        ("exchange_qty", math.nan, 1e-9),
        ("tolerance", 0.01, float("inf")),
    ],
)
def test_live_position_reconcile_rejects_nonfinite_inputs_without_raising(tmp_path, field, exchange_qty, tolerance):
    db = str(tmp_path / "execution.sqlite")
    s = LivePositionStore(db)

    out = s.reconcile_to_exchange(
        venue="coinbase",
        symbol="BTC/USD",
        exchange_qty=exchange_qty,
        tolerance=tolerance,
    )

    assert out["ok"] is False
    assert out["reason"].startswith(f"invalid_live_position_numeric:{field}:")
    assert out["drift"] is None
