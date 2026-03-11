from __future__ import annotations

from services.backtest.parity_engine import run_backtest, run_parity_backtest


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


def test_legacy_run_backtest_wrapper_still_returns_truthy_signals():
    values = [1, 2, 3, 4, 5]

    def _fn(v: int):
        return {"v": v} if v % 2 == 0 else None

    out = run_backtest(_fn, values)
    assert out == [{"v": 2}, {"v": 4}]

