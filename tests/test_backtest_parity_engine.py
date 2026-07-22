from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.backtest import parity_engine
from services.backtest.parity_engine import run_backtest, run_parity_backtest
from storage.paper_trading_sqlite import PaperTradingSQLite


def _candles(closes: list[float]) -> list[list[float]]:
    rows: list[list[float]] = []
    if not closes:
        return rows
    prev = float(closes[0])
    for i, close in enumerate(closes):
        c = float(close)
        o = float(prev)
        h = max(o, c) + 0.2
        l = min(o, c) - 0.2
        rows.append([i * 60_000, o, h, l, c, 1.0])
        prev = c
    return rows


def _paper_order(order_id: str, *, side: str, qty: float) -> dict:
    return {
        "order_id": order_id,
        "client_order_id": f"client-{order_id}",
        "ts": "2026-07-22T00:00:00Z",
        "venue": "paper",
        "symbol": "BTC/USD",
        "side": side,
        "order_type": "market",
        "qty": qty,
        "limit_price": None,
        "status": "new",
        "reject_reason": None,
        "strategy_id": "ema_cross",
        "meta": None,
    }


def test_parity_backtest_round_trip_matches_paper_storage_net_pnl(monkeypatch, tmp_path):
    def fake_signal(*, cfg, symbol, ohlcv):
        action = "buy" if len(ohlcv) == 1 else "sell" if len(ohlcv) == 2 else "hold"
        return {"ok": True, "action": action, "strategy": "ema_cross", "symbol": symbol, "reason": f"test:{action}"}

    monkeypatch.setattr(parity_engine, "compute_signal", fake_signal)

    initial_cash = 1_000.0
    out = run_parity_backtest(
        cfg={"strategy": {"name": "ema_cross"}},
        symbol="BTC/USD",
        candles=_candles([100.0, 103.0]),
        warmup_bars=1,
        initial_cash=initial_cash,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert out["buy_count"] == 1
    assert out["sell_count"] == 1
    assert out["metrics"]["closed_trades"] == 1
    buy_trade, sell_trade = out["trades"]

    import storage.paper_trading_sqlite as paper_store

    monkeypatch.setattr(paper_store, "DB_PATH", tmp_path / "paper_trading.sqlite")
    db = PaperTradingSQLite()
    db.set_state("cash_quote", str(initial_cash))
    db.set_state("realized_pnl", "0.0")

    buy_order = _paper_order("parity-buy", side="buy", qty=float(buy_trade["qty"]))
    db.insert_order(buy_order)
    buy = db.apply_fill(
        order=buy_order,
        ts="2026-07-22T00:00:01Z",
        price=float(buy_trade["exec_px"]),
        qty=float(buy_trade["qty"]),
        fee=float(buy_trade["fee"]),
        fee_currency="USD",
    )
    assert buy["ok"] is True

    sell_order = _paper_order("parity-sell", side="sell", qty=float(sell_trade["qty"]))
    db.insert_order(sell_order)
    sell = db.apply_fill(
        order=sell_order,
        ts="2026-07-22T00:00:02Z",
        price=float(sell_trade["exec_px"]),
        qty=float(sell_trade["qty"]),
        fee=float(sell_trade["fee"]),
        fee_currency="USD",
    )

    assert sell["ok"] is True
    assert sell["pnl_usd_semantics"] == "net_of_fees"
    assert sell["realized_pnl_usd"] == pytest.approx(float(sell_trade["realized_pnl"]))
    assert float(db.get_state("realized_pnl") or "nan") == pytest.approx(out["metrics"]["realized_pnl"])
    assert float(db.get_state("cash_quote") or "nan") == pytest.approx(float(sell_trade["cash_after"]))

    pos = db.get_position("BTC/USD")
    assert pos is not None
    assert pos["qty"] == pytest.approx(0.0)
    assert pos["realized_pnl"] == pytest.approx(out["metrics"]["realized_pnl"])
    assert out["metrics"]["final_equity"] == pytest.approx(float(db.get_state("cash_quote") or "nan"))


def test_run_parity_backtest_ema_cross_outputs_metrics_and_trades():
    prices = [
        100,
        99,
        98,
        97,
        96,
        95,
        94,
        93,
        92,
        91,
        90,
        91,
        92,
        93,
        94,
        95,
        96,
        97,
        98,
        99,
        100,
        99,
        98,
        97,
        96,
        95,
        94,
        93,
        92,
        91,
        90,
    ]
    out = run_parity_backtest(
        cfg={"strategy": {"name": "ema_cross", "ema_fast": 3, "ema_slow": 5}},
        symbol="BTC/USD",
        candles=_candles(prices),
        warmup_bars=5,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    assert out["ok"] is True
    assert out["strategy"] == "ema_cross"
    assert out["buy_count"] >= 1
    assert out["sell_count"] >= 1
    assert out["trade_count"] == out["buy_count"] + out["sell_count"]
    assert len(out["equity"]) == len(prices)
    assert float(out["metrics"]["final_equity"]) > 0.0
    assert float(out["metrics"]["total_fees"]) > 0.0
    scorecard = out["scorecard"]
    assert scorecard["strategy"] == "ema_cross"
    assert scorecard["symbol"] == "BTC/USD"
    assert "net_return_after_costs_pct" in scorecard
    assert "profit_factor" in scorecard
    assert "exposure_adjusted_return_pct" in scorecard
    assert len(out["regimes"]) == len(prices)
    assert set(out["regime_scorecards"].keys()) == {"bull", "bear", "chop", "high_vol", "low_vol"}


def test_run_parity_backtest_supports_new_strategies():
    mr = run_parity_backtest(
        cfg={"strategy": {"name": "mean_reversion_rsi", "rsi_len": 5, "sma_len": 5, "rsi_buy": 35.0, "rsi_sell": 65.0}},
        symbol="BTC/USD",
        candles=_candles(
            [
                100,
                99,
                98,
                97,
                96,
                95,
                94,
                93,
                92,
                91,
                90,
                91,
                92,
                93,
                94,
                95,
                96,
                97,
                98,
                99,
                100,
                101,
                102,
                103,
                104,
                103,
                102,
                101,
                100,
                99,
                98,
                97,
                96,
            ]
        ),
        warmup_bars=5,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    assert mr["ok"] is True
    assert mr["strategy"] == "mean_reversion_rsi"
    assert mr["trade_count"] >= 2
    assert mr["signal_count"] >= mr["trade_count"]

    bo = run_parity_backtest(
        cfg={"strategy": {"name": "breakout_donchian", "donchian_len": 5}},
        symbol="BTC/USD",
        candles=_candles(
            [
                100,
                100,
                100,
                100,
                100,
                100,
                100,
                103,
                104,
                105,
                106,
                106,
                106,
                105,
                104,
                103,
                102,
                101,
                100,
                99,
                98,
                97,
                96,
            ]
        ),
        warmup_bars=5,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    assert bo["ok"] is True
    assert bo["strategy"] == "breakout_donchian"
    assert bo["trade_count"] >= 2
    assert bo["buy_count"] >= 1
    assert bo["sell_count"] >= 1


def test_run_parity_backtest_sma_200_trend_closes_round_trip_on_flat_signal():
    closes = (
        [100.0] * 62
        + [100.2, 100.4, 100.6, 100.8, 101.0, 101.2, 101.4, 101.6]
        + [99.0, 98.8, 98.6, 98.4, 98.2, 98.0]
    )

    out = run_parity_backtest(
        cfg={"strategy": {"name": "sma_200_trend", "sma_period": 5, "atr_period": 2}},
        symbol="BTC/USD",
        candles=_candles(closes),
        warmup_bars=62,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert out["ok"] is True
    assert out["strategy"] == "sma_200_trend"
    assert out["buy_count"] >= 1
    assert out["sell_count"] >= 1
    assert out["metrics"]["closed_trades"] >= 1
    assert any(str(trade.get("reason") or "").startswith("sma200:flat") for trade in out["trades"])
    assert "avg_win" in out["scorecard"]
    assert "avg_loss" in out["scorecard"]


def test_run_parity_backtest_sma_200_trend_fixture_closes_default_round_trip():
    fixture = Path("sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json")
    rows = json.loads(fixture.read_text(encoding="utf-8"))

    out = run_parity_backtest(
        cfg={"strategy": {"name": "sma_200_trend", "sma_period": 200, "atr_period": 20}},
        symbol="BTC/USDT",
        candles=rows,
        warmup_bars=210,
        initial_cash=1_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert len(rows) == 220
    assert out["ok"] is True
    assert out["strategy"] == "sma_200_trend"
    assert out["buy_count"] == 1
    assert out["sell_count"] == 1
    assert out["metrics"]["closed_trades"] == 1
    assert out["signals"][0]["reason"].startswith("sma200:long")
    assert out["trades"][-1]["reason"].startswith("sma200:flat")
    assert out["scorecard"]["closed_trades"] == 1
    assert "avg_win" in out["scorecard"]
    assert "avg_loss" in out["scorecard"]


def test_run_parity_backtest_skips_malformed_rows_and_stays_deterministic():
    candles = [
        [0, 100, 101, 99, 100, 1],
        [1],  # malformed
        "bad",  # malformed
        [60_000, 101, 102, 100, 101, 1],
    ]
    out = run_parity_backtest(
        cfg={"strategy": {"name": "ema_cross", "ema_fast": 2, "ema_slow": 3}},
        symbol="BTC/USD",
        candles=candles,
        warmup_bars=1,
    )
    assert out["ok"] is True
    assert out["bars"] == 2
    assert len(out["equity"]) == 2


def test_run_parity_backtest_treats_none_strategy_cfg_as_default():
    out = run_parity_backtest(
        cfg={"strategy": None},
        symbol="BTC/USD",
        candles=_candles([100, 101, 102, 103]),
        warmup_bars=1,
    )
    assert out["ok"] is True
    assert out["strategy"] == "ema_cross"
    assert out["bars"] == 4


def test_legacy_run_backtest_wrapper_still_returns_truthy_signals():
    values = [1, 2, 3, 4, 5]

    def _fn(v: int):
        return {"v": v} if v % 2 == 0 else None

    out = run_backtest(_fn, values)
    assert out == [{"v": 2}, {"v": 4}]
