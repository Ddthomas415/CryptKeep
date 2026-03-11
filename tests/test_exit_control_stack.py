from __future__ import annotations

from services.risk.exit_controls import evaluate_strategy_exit_stack


def test_exit_stack_prioritizes_stop_loss():
    out = evaluate_strategy_exit_stack(
        entry_price=100.0,
        current_price=90.0,
        qty=1.0,
        side="long",
        strategy="ema_cross",
        stop_loss_pct=0.05,
        take_profit_pct=0.20,
    )
    assert out["action"] == "exit"
    assert out["stack_rule"] == "stop_loss"
    assert "stop_loss" in out["reason"]


def test_exit_stack_trailing_stop_for_long():
    out = evaluate_strategy_exit_stack(
        entry_price=100.0,
        current_price=102.0,
        qty=1.0,
        side="long",
        strategy="mean_reversion",
        trailing_peak_price=110.0,
        trailing_stop_pct=0.05,
    )
    assert out["action"] == "exit"
    assert out["stack_rule"] == "trailing_stop"


def test_exit_stack_take_profit_when_no_other_exit():
    out = evaluate_strategy_exit_stack(
        entry_price=100.0,
        current_price=112.0,
        qty=1.0,
        side="long",
        strategy="breakout",
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
    )
    assert out["action"] == "exit"
    assert out["stack_rule"] == "take_profit"


def test_exit_stack_time_stop_when_limits_not_hit():
    out = evaluate_strategy_exit_stack(
        entry_price=100.0,
        current_price=101.0,
        qty=1.0,
        side="long",
        strategy="ema_cross",
        bars_held=50,
        max_bars_hold=20,
    )
    assert out["action"] == "exit"
    assert out["stack_rule"] == "time_stop"


def test_exit_stack_holds_when_no_rule_triggers():
    out = evaluate_strategy_exit_stack(
        entry_price=100.0,
        current_price=101.0,
        qty=1.0,
        side="long",
        strategy="ema_cross",
        stop_loss_pct=0.10,
        take_profit_pct=0.20,
        trailing_peak_price=103.0,
        trailing_stop_pct=0.05,
        bars_held=3,
        max_bars_hold=20,
    )
    assert out["action"] == "hold"
    assert out["stack_rule"] == "none"
