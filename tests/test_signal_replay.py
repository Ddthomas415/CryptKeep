from services.backtest.signal_replay import replay_signals_on_ohlcv


def test_replay_signals_on_ohlcv_minimal():
    ohlcv = [
        [1000, 100.0, 101.0, 99.0, 100.0, 1.0],
        [2000, 110.0, 111.0, 109.0, 110.0, 1.0],
    ]
    signals = [
        {"ts_ms": 1000, "action": "buy"},
        {"ts_ms": 2000, "action": "sell"},
    ]

    out = replay_signals_on_ohlcv(
        ohlcv,
        signals,
        fee_bps=0.0,
        slippage_bps=0.0,
        initial_cash=10000.0,
    )

    assert out["initial_cash"] == 10000.0
    assert out["signals_used"] == 2
    assert len(out["trades"]) == 2
    assert len(out["equity"]) == 2
    assert out["final_equity"] == 11000.0
    assert out["realized_pnl_est"] == 1000.0
