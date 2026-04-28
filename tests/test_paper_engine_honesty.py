from services.execution.paper_engine import PaperEngine


def test_paper_submit_order_can_fill_in_same_call(monkeypatch, tmp_path):
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
    assert out["order"]["status"] == "filled"

    fills = eng.db.list_fills(limit=10)
    assert len(fills) == 1
    assert fills[0]["order_id"] == out["order"]["order_id"]
