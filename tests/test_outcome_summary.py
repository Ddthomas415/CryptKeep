from services.execution.outcome_summary import summarize_closed_trade_outcomes


def test_closed_trade_summary_preserves_exit_attribution() -> None:
    summary = summarize_closed_trade_outcomes(
        [
            {
                "journal_ts": "2026-06-11T00:03:20Z",
                "symbol": "BTC/USDT",
                "selected_strategy": "breakout_donchian",
                "regime": "low_volatility",
                "side": "buy",
                "pos_qty": 0.001,
                "realized_pnl_total": 0.0,
            },
            {
                "journal_ts": "2026-06-11T00:06:02Z",
                "symbol": "BTC/USDT",
                "selected_strategy": "breakout_donchian",
                "regime": "low_volatility",
                "side": "sell",
                "signal_reason": "no_signal",
                "exit_reason": "strategy_exit:breakout_donchian:time_stop",
                "exit_stack_rule": "time_stop",
                "pos_qty": 0.0,
                "realized_pnl_total": -0.0421,
            },
        ]
    )

    assert summary["count"] == 1
    assert summary["closed_rows"][0]["signal_reason"] == "no_signal"
    assert summary["closed_rows"][0]["exit_reason"] == "strategy_exit:breakout_donchian:time_stop"
    assert summary["closed_rows"][0]["exit_stack_rule"] == "time_stop"
