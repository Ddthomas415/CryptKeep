from __future__ import annotations

import importlib

import pytest


def _reload_paper_store(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    import services.os.app_paths as app_paths
    import storage.paper_trading_sqlite as paper_store

    importlib.reload(app_paths)
    importlib.reload(paper_store)
    return paper_store


def _order(order_id: str, *, side: str, qty: float) -> dict:
    return {
        "order_id": order_id,
        "client_order_id": f"client-{order_id}",
        "ts": "2026-07-04T00:00:00Z",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": side,
        "order_type": "market",
        "qty": qty,
        "limit_price": None,
        "status": "new",
        "reject_reason": None,
        "strategy_id": "sma_200_trend",
        "meta": None,
    }


def _insert_order(db, order_id: str, *, side: str, qty: float) -> dict:
    row = _order(order_id, side=side, qty=qty)
    db.insert_order(row)
    return row


def test_apply_fill_mixed_sequence_reconciles_cash_position_and_realized_pnl(monkeypatch, tmp_path):
    paper_store = _reload_paper_store(monkeypatch, tmp_path)
    db = paper_store.PaperTradingSQLite()
    db.set_state("cash_quote", "1000.0")
    db.set_state("realized_pnl", "0.0")

    buy_order = _insert_order(db, "buy-2-btc", side="buy", qty=2.0)
    buy = db.apply_fill(
        order=buy_order,
        ts="2026-07-04T00:00:01Z",
        price=100.0,
        qty=2.0,
        fee=0.20,
        fee_currency="USD",
    )
    assert buy["ok"] is True
    assert buy["realized_pnl_usd"] == 0.0
    assert buy["pnl_usd_semantics"] == "net_of_fees"

    sell_order = _insert_order(db, "sell-1-btc", side="sell", qty=1.0)
    sell = db.apply_fill(
        order=sell_order,
        ts="2026-07-04T00:00:02Z",
        price=110.0,
        qty=1.0,
        fee=0.11,
        fee_currency="USD",
    )

    expected_avg = (100.0 * 2.0 + 0.20) / 2.0
    expected_realized = (110.0 * 1.0 - 0.11) - expected_avg
    expected_cash = 1000.0 - (100.0 * 2.0 + 0.20) + (110.0 * 1.0 - 0.11)

    assert sell["ok"] is True
    assert sell["realized_pnl_usd"] == pytest.approx(expected_realized)
    assert sell["pnl_usd_semantics"] == "net_of_fees"
    assert float(db.get_state("cash_quote") or "nan") == pytest.approx(expected_cash)
    assert float(db.get_state("realized_pnl") or "nan") == pytest.approx(expected_realized)

    pos = db.get_position("BTC/USD")
    assert pos is not None
    assert pos["qty"] == pytest.approx(1.0)
    assert pos["avg_price"] == pytest.approx(expected_avg)
    assert pos["realized_pnl"] == pytest.approx(expected_realized)

    fills = db.list_fills(limit=10)
    assert len(fills) == 2
    assert sum(float(fill["fee"]) for fill in fills) == pytest.approx(0.31)
    order_statuses = {
        db.get_order_by_order_id(order_id)["status"]
        for order_id in ("buy-2-btc", "sell-1-btc")
    }
    assert order_statuses == {"filled"}


def test_apply_fill_flat_round_trip_with_fees_is_net_negative(monkeypatch, tmp_path):
    paper_store = _reload_paper_store(monkeypatch, tmp_path)
    db = paper_store.PaperTradingSQLite()
    db.set_state("cash_quote", "1000.0")
    db.set_state("realized_pnl", "0.0")

    buy_order = _insert_order(db, "flat-buy", side="buy", qty=1.0)
    db.apply_fill(
        order=buy_order,
        ts="2026-07-04T00:00:01Z",
        price=100.0,
        qty=1.0,
        fee=0.10,
        fee_currency="USD",
    )

    sell_order = _insert_order(db, "flat-sell", side="sell", qty=1.0)
    sell = db.apply_fill(
        order=sell_order,
        ts="2026-07-04T00:00:02Z",
        price=100.0,
        qty=1.0,
        fee=0.10,
        fee_currency="USD",
    )

    assert sell["ok"] is True
    assert sell["realized_pnl_usd"] == pytest.approx(-0.20)
    assert sell["pnl_usd_semantics"] == "net_of_fees"
    assert float(db.get_state("cash_quote") or "nan") == pytest.approx(999.80)
    assert float(db.get_state("realized_pnl") or "nan") == pytest.approx(-0.20)

    pos = db.get_position("BTC/USD")
    assert pos is not None
    assert pos["qty"] == pytest.approx(0.0)
    assert pos["avg_price"] == pytest.approx(0.0)
    assert pos["realized_pnl"] == pytest.approx(-0.20)
