from services.risk.exit_controls import evaluate_strategy_exit_stack


def test_breakout_exit_stack_stop_loss():
    out = evaluate_strategy_exit_stack(
        entry_price=100.0,
        current_price=96.0,
        qty=1.0,
        side="long",
        strategy="breakout_donchian",
        stop_loss_pct=0.03,
        take_profit_pct=0.06,
        trailing_peak_price=101.0,
        trailing_stop_pct=0.02,
        bars_held=5,
        max_bars_hold=60,
    )
    assert out["action"] == "exit"
    assert out["stack_rule"] == "stop_loss"


def test_breakout_exit_stack_trailing_stop():
    out = evaluate_strategy_exit_stack(
        entry_price=100.0,
        current_price=107.0,
        qty=1.0,
        side="long",
        strategy="breakout_donchian",
        stop_loss_pct=0.03,
        take_profit_pct=0.20,
        trailing_peak_price=110.0,
        trailing_stop_pct=0.02,
        bars_held=10,
        max_bars_hold=60,
    )
    assert out["action"] == "exit"
    assert out["stack_rule"] == "trailing_stop"


def test_breakout_exit_stack_time_stop():
    out = evaluate_strategy_exit_stack(
        entry_price=100.0,
        current_price=100.5,
        qty=1.0,
        side="long",
        strategy="breakout_donchian",
        stop_loss_pct=0.03,
        take_profit_pct=0.06,
        trailing_peak_price=101.0,
        trailing_stop_pct=0.02,
        bars_held=60,
        max_bars_hold=60,
    )
    assert out["action"] == "exit"
    assert out["stack_rule"] == "time_stop"
