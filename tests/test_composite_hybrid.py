from __future__ import annotations

from services.strategies.composite_hybrid import STRATEGY_ID, combine_confirmation_gate
from services.strategies.strategy_registry import SUPPORTED


def test_confirmation_gate_buys_only_when_primary_and_confirmer_are_bullish() -> None:
    result = combine_confirmation_gate(
        symbol="BTC/USDT",
        primary_name="breakout_donchian",
        primary_signal={"ok": True, "action": "buy", "reason": "donchian_break_up", "confidence": 0.8},
        confirmer_name="sma_200_trend",
        confirmer_signal={"ok": True, "action": "hold", "direction": "bullish", "confidence": 0.7},
    )

    assert result["ok"] is True
    assert result["strategy"] == STRATEGY_ID
    assert result["action"] == "buy"
    assert result["reason"] == "confirmation_gate_entry"
    assert result["selected_child"] == "primary"
    assert result["confidence"] == 0.7
    assert result["risk_flags"] == []


def test_confirmation_gate_blocks_entry_when_confirmer_is_not_bullish() -> None:
    result = combine_confirmation_gate(
        symbol="BTC/USDT",
        primary_name="breakout_donchian",
        primary_signal={"ok": True, "action": "buy", "confidence": 0.9},
        confirmer_name="sma_200_trend",
        confirmer_signal={"ok": True, "action": "hold", "direction": "neutral"},
    )

    assert result["action"] == "hold"
    assert result["reason"] == "confirmer_not_bullish"
    assert "confirmer_not_bullish" in result["rule_path"]


def test_confirmation_gate_does_not_convert_sell_to_short_entry() -> None:
    result = combine_confirmation_gate(
        symbol="BTC/USDT",
        primary_name="breakout_donchian",
        primary_signal={"ok": True, "action": "sell", "confidence": 0.9},
        confirmer_name="sma_200_trend",
        confirmer_signal={"ok": True, "action": "sell", "confidence": 0.8},
        position_open=False,
    )

    assert result["action"] == "hold"
    assert result["reason"] == "sell_ignored_without_position"
    assert "short_entry_blocked" in result["risk_flags"]


def test_confirmation_gate_does_not_mask_primary_exit() -> None:
    result = combine_confirmation_gate(
        symbol="BTC/USDT",
        primary_name="breakout_donchian",
        primary_signal={"ok": True, "action": "sell", "confidence": 0.9},
        confirmer_name="sma_200_trend",
        confirmer_signal={"ok": True, "action": "hold", "direction": "bullish"},
        position_open=True,
    )

    assert result["action"] == "sell"
    assert result["reason"] == "primary_exit"
    assert result["selected_child"] == "primary"


def test_confirmation_gate_does_not_mask_confirmer_exit() -> None:
    result = combine_confirmation_gate(
        symbol="BTC/USDT",
        primary_name="breakout_donchian",
        primary_signal={"ok": True, "action": "hold"},
        confirmer_name="sma_200_trend",
        confirmer_signal={"ok": True, "action": "sell", "confidence": 0.75},
        position_open=True,
    )

    assert result["action"] == "sell"
    assert result["reason"] == "confirmer_exit"
    assert result["selected_child"] == "confirmer"
    assert result["confidence"] == 0.75


def test_confirmation_gate_risk_exit_takes_precedence() -> None:
    result = combine_confirmation_gate(
        symbol="BTC/USDT",
        primary_name="breakout_donchian",
        primary_signal={"ok": True, "action": "buy"},
        confirmer_name="sma_200_trend",
        confirmer_signal={"ok": True, "action": "buy"},
        position_open=True,
        risk_exit={"reason": "max_drawdown_exit"},
    )

    assert result["action"] == "sell"
    assert result["reason"] == "max_drawdown_exit"
    assert result["selected_child"] == "risk_exit"
    assert result["rule_path"] == ["confirmation_gate", "risk_exit"]


def test_confirmation_gate_holds_on_invalid_or_short_child_signal() -> None:
    result = combine_confirmation_gate(
        symbol="BTC/USDT",
        primary_name="experimental_child",
        primary_signal={"ok": True, "action": "short", "confidence": 1.0},
        confirmer_name="sma_200_trend",
        confirmer_signal={"ok": True, "action": "buy"},
    )

    assert result["action"] == "hold"
    assert result["reason"] == "primary_no_entry"
    assert "primary:short_signal_blocked" in result["risk_flags"]


def test_composite_hybrid_not_registered_as_runtime_strategy_yet() -> None:
    assert STRATEGY_ID not in SUPPORTED
    assert "composite_hybrid" not in SUPPORTED
