import pytest

from services.execution.fill_model import apply_fee_slippage
from services.execution.paper_engine import PaperEngine


def test_paper_submit_order_requires_explicit_fill_evaluation(monkeypatch, tmp_path):
    import storage.paper_trading_sqlite as paper_store

    monkeypatch.setattr(paper_store, "DB_PATH", tmp_path / "paper_trading.sqlite")

    monkeypatch.setattr(
        "services.execution.paper_engine.load_user_yaml",
        lambda: {
            "paper_trading": {
                "enabled": True,
                "starting_cash_quote": 10000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    monkeypatch.setattr(
        "services.execution.paper_engine.get_best_bid_ask_last",
        lambda venue, symbol: {"bid": 99.0, "ask": 101.0, "last": 100.0},
    )
    monkeypatch.setattr("services.execution.paper_engine.is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr("services.execution.paper_engine.is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(
        "services.execution.paper_engine.check_market_quality",
        lambda venue, symbol: {"ok": True, "reason": "ok", "price_used": 100.0},
    )
    monkeypatch.setattr("services.execution.paper_engine.should_allow_order", lambda *args, **kwargs: (True, "ok"))

    eng = PaperEngine(clock=lambda: "2026-01-01T00:00:00+00:00")

    out = eng.submit_order(
        client_order_id="cid-1",
        venue="paper",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
        ts="2026-01-01T00:00:00+00:00",
    )

    assert out["ok"] is True
    assert out["order"]["status"] == "new"

    fills = eng.db.list_fills(limit=10)
    assert fills == []

    rec = eng.evaluate_open_orders()
    assert rec["open_orders_seen"] == 1
    assert rec["filled"] == 1

    out = eng.db.get_order_by_client_id("cid-1")
    assert out is not None
    assert out["status"] == "filled"

    fills = eng.db.list_fills(limit=10)
    assert len(fills) == 1
    assert fills[0]["order_id"] == out["order_id"]


def test_paper_market_fills_match_shared_fee_slippage_model(monkeypatch, tmp_path):
    import storage.paper_trading_sqlite as paper_store

    monkeypatch.setattr(paper_store, "DB_PATH", tmp_path / "paper_trading.sqlite")

    monkeypatch.setattr(
        "services.execution.paper_engine.load_user_yaml",
        lambda: {
            "paper_trading": {
                "enabled": True,
                "starting_cash_quote": 10000.0,
                "fee_bps": 10.0,
                "slippage_bps": 5.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    monkeypatch.setattr(
        "services.execution.paper_engine.get_best_bid_ask_last",
        lambda venue, symbol: {"bid": 99.0, "ask": 101.0, "last": 100.0},
    )
    monkeypatch.setattr("services.execution.paper_engine.is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr("services.execution.paper_engine.is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(
        "services.execution.paper_engine.check_market_quality",
        lambda venue, symbol: {"ok": True, "reason": "ok", "price_used": 100.0},
    )
    monkeypatch.setattr("services.execution.paper_engine.should_allow_order", lambda *args, **kwargs: (True, "ok"))

    eng = PaperEngine(clock=lambda: "2026-01-01T00:00:00+00:00")

    buy = eng.submit_order(
        client_order_id="buy-1",
        venue="paper",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=2.0,
        ts="2026-01-01T00:00:00+00:00",
    )
    assert buy["ok"] is True
    assert eng.evaluate_open_orders()["filled"] == 1
    buy_order = eng.db.get_order_by_client_id("buy-1")
    buy_fill = eng.db.list_fills_for_order(str(buy_order["order_id"]))[0]
    expected_buy = apply_fee_slippage(
        mid_px=100.0,
        side="buy",
        qty=2.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    assert buy_fill["price"] == pytest.approx(expected_buy.exec_px)
    assert buy_fill["fee"] == pytest.approx(expected_buy.fee)

    sell = eng.submit_order(
        client_order_id="sell-1",
        venue="paper",
        symbol="BTC/USD",
        side="sell",
        order_type="market",
        qty=2.0,
        ts="2026-01-01T00:01:00+00:00",
    )
    assert sell["ok"] is True
    assert eng.evaluate_open_orders()["filled"] == 1
    sell_order = eng.db.get_order_by_client_id("sell-1")
    sell_fill = eng.db.list_fills_for_order(str(sell_order["order_id"]))[0]
    expected_sell = apply_fee_slippage(
        mid_px=100.0,
        side="sell",
        qty=2.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    assert sell_fill["price"] == pytest.approx(expected_sell.exec_px)
    assert sell_fill["fee"] == pytest.approx(expected_sell.fee)
