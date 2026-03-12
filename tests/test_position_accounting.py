from services.portfolio.position_accounting import PositionAccounting


def test_apply_fill_buy_updates_position_and_cash():
    pa = PositionAccounting()

    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 2, "price": 100})

    snap = pa.snapshot()
    assert snap["cash"]["USD"] == -200.0
    assert snap["realized"] == 0.0
    assert snap["unrealized"] == 0.0
    assert snap["positions"] == [
        {
            "symbol": "BTC/USD",
            "base": "BTC",
            "quote": "USD",
            "qty": 2.0,
            "avg_price": 100.0,
            "mark_price": None,
            "unrealized": None,
        }
    ]


def test_apply_fill_multiple_buys_reprices_average_cost():
    pa = PositionAccounting()

    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 200})

    snap = pa.snapshot()
    assert snap["cash"]["USD"] == -300.0
    assert snap["positions"][0]["qty"] == 2.0
    assert snap["positions"][0]["avg_price"] == 150.0


def test_apply_fill_sell_realizes_pnl_and_restores_cash():
    pa = PositionAccounting()

    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 2, "price": 100})
    pa.apply_fill({"side": "SELL", "symbol": "BTC/USD", "qty": 1, "price": 130})

    snap = pa.snapshot()
    assert snap["cash"]["USD"] == -70.0
    assert snap["realized"] == 30.0
    assert snap["positions"][0]["qty"] == 1.0
    assert snap["positions"][0]["avg_price"] == 100.0


def test_apply_fill_sell_all_zeroes_position():
    pa = PositionAccounting()

    pa.apply_fill({"side": "BUY", "symbol": "ETH/USD", "qty": 3, "price": 50})
    pa.apply_fill({"side": "SELL", "symbol": "ETH/USD", "qty": 3, "price": 60})

    snap = pa.snapshot()
    assert snap["cash"]["USD"] == 30.0
    assert snap["realized"] == 30.0
    assert snap["positions"][0]["qty"] == 0.0
    assert snap["positions"][0]["avg_price"] == 0.0


def test_apply_fill_sell_more_than_position_raises():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})

    try:
        pa.apply_fill({"side": "SELL", "symbol": "BTC/USD", "qty": 2, "price": 110})
        assert False, "expected ValueError"
    except ValueError as e:
        assert "exceeds current position" in str(e)


def test_apply_fill_rejects_invalid_fill():
    pa = PositionAccounting()

    for fill in (
        {"side": "HOLD", "symbol": "BTC/USD", "qty": 1, "price": 100},
        {"side": "BUY", "symbol": "BTCUSD", "qty": 1, "price": 100},
        {"side": "BUY", "symbol": "BTC/USD", "qty": 0, "price": 100},
    ):
        try:
            pa.apply_fill(fill)
            assert False, "expected ValueError"
        except ValueError:
            pass

def test_snapshot_with_marks_computes_unrealized_gain():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 2, "price": 100})

    snap = pa.snapshot(marks={"BTC/USD": 125})

    assert snap["unrealized"] == 50.0
    assert snap["positions"][0]["mark_price"] == 125.0
    assert snap["positions"][0]["unrealized"] == 50.0


def test_snapshot_with_marks_computes_unrealized_loss():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "ETH/USD", "qty": 3, "price": 50})

    snap = pa.snapshot(marks={"ETH/USD": 40})

    assert snap["unrealized"] == -30.0
    assert snap["positions"][0]["mark_price"] == 40.0
    assert snap["positions"][0]["unrealized"] == -30.0


def test_snapshot_without_marks_keeps_unrealized_zero_and_mark_none():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})

    snap = pa.snapshot()

    assert snap["unrealized"] == 0.0
    assert snap["positions"][0]["mark_price"] is None
    assert snap["positions"][0]["unrealized"] is None


def test_snapshot_with_marks_includes_equity_by_quote():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 2, "price": 100})

    snap = pa.snapshot(marks={"BTC/USD": 125})

    assert snap["cash"]["USD"] == -200.0
    assert snap["equity_by_quote"]["USD"] == 50.0


def test_snapshot_without_marks_equity_by_quote_matches_cash_only():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})

    snap = pa.snapshot()

    assert snap["cash"]["USD"] == -100.0
    assert snap["equity_by_quote"]["USD"] == -100.0


def test_snapshot_equity_by_quote_handles_realized_and_open_position():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "ETH/USD", "qty": 3, "price": 50})
    pa.apply_fill({"side": "SELL", "symbol": "ETH/USD", "qty": 1, "price": 70})

    snap = pa.snapshot(marks={"ETH/USD": 60})

    assert snap["cash"]["USD"] == -80.0
    assert snap["realized"] == 20.0
    assert snap["unrealized"] == 20.0
    assert snap["equity_by_quote"]["USD"] == 40.0


def test_snapshot_single_quote_sets_total_equity():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 2, "price": 100})

    snap = pa.snapshot(marks={"BTC/USD": 125})

    assert snap["equity_by_quote"]["USD"] == 50.0
    assert snap["total_equity"] == 50.0
    assert snap["fx_conversion"]["complete"] is True


def test_snapshot_without_marks_single_quote_total_equity_matches_cash():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})

    snap = pa.snapshot()

    assert snap["equity_by_quote"]["USD"] == -100.0
    assert snap["total_equity"] == -100.0
    assert snap["fx_conversion"]["complete"] is True


def test_snapshot_multi_quote_leaves_total_equity_none():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})
    pa.apply_fill({"side": "BUY", "symbol": "ETH/USDT", "qty": 2, "price": 50})

    snap = pa.snapshot(marks={"BTC/USD": 120, "ETH/USDT": 60})

    assert snap["equity_by_quote"]["USD"] == 20.0
    assert snap["equity_by_quote"]["USDT"] == 20.0
    assert snap["total_equity"] is None
    assert snap["fx_conversion"]["complete"] is False


def test_snapshot_multi_quote_sets_total_equity_when_target_quote_and_fx_marks_given():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})
    pa.apply_fill({"side": "BUY", "symbol": "ETH/USDT", "qty": 2, "price": 50})

    snap = pa.snapshot(
        marks={"BTC/USD": 120, "ETH/USDT": 60},
        target_quote="USD",
        quote_marks={"USDT/USD": 1.0},
    )

    assert snap["equity_by_quote"]["USD"] == 20.0
    assert snap["equity_by_quote"]["USDT"] == 20.0
    assert snap["total_equity"] == 40.0
    assert snap["fx_conversion"]["complete"] is True
    used = snap["fx_conversion"]["used"]
    assert any(u["method"] == "direct" for u in used)


def test_snapshot_multi_quote_leaves_total_equity_none_when_fx_mark_missing():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})
    pa.apply_fill({"side": "BUY", "symbol": "ETH/USDT", "qty": 2, "price": 50})

    snap = pa.snapshot(
        marks={"BTC/USD": 120, "ETH/USDT": 60},
        target_quote="USD",
    )

    assert snap["equity_by_quote"]["USD"] == 20.0
    assert snap["equity_by_quote"]["USDT"] == 20.0
    assert snap["total_equity"] is None
    assert snap["fx_conversion"]["complete"] is False
    assert len(snap["fx_conversion"]["missing"]) >= 1


def test_snapshot_multi_quote_supports_inverse_fx_mark():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})
    pa.apply_fill({"side": "BUY", "symbol": "ETH/USDT", "qty": 2, "price": 50})

    snap = pa.snapshot(
        marks={"BTC/USD": 120, "ETH/USDT": 60},
        target_quote="USD",
        quote_marks={"USD/USDT": 1.0},
    )

    assert snap["equity_by_quote"]["USD"] == 20.0
    assert snap["equity_by_quote"]["USDT"] == 20.0
    assert snap["total_equity"] == 40.0
    used = snap["fx_conversion"]["used"]
    assert any(u["method"] == "inverse" for u in used)


def test_snapshot_target_quote_and_fx_pairs_are_case_insensitive():
    pa = PositionAccounting()
    pa.apply_fill({"side": "BUY", "symbol": "BTC/USD", "qty": 1, "price": 100})
    pa.apply_fill({"side": "BUY", "symbol": "ETH/USDT", "qty": 2, "price": 50})

    snap = pa.snapshot(
        marks={"BTC/USD": 120, "ETH/USDT": 60},
        target_quote="usd",
        quote_marks={"usdt/usd": 1.0},
    )
    assert snap["total_equity"] == 40.0
    assert snap["fx_conversion"]["target_quote"] == "USD"
