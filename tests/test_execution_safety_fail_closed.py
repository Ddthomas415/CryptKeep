from __future__ import annotations

import pytest

import services.execution.safety as safety
from services.config_loader import ConfigLoadError


def test_load_gates_uses_strict_runtime_config(monkeypatch):
    calls: list[bool] = []

    def fake_load_user_config(*, strict: bool = False):
        calls.append(strict)
        return {"safety": {"min_order_notional": 10.0}}

    monkeypatch.setattr(safety, "load_user_config", fake_load_user_config)

    gates = safety.load_gates()

    assert calls == [True]
    assert gates.min_order_notional == 10.0


def test_load_gates_propagates_corrupt_config(monkeypatch):
    def fake_load_user_config(*, strict: bool = False):
        raise ConfigLoadError("config_load_failed:/tmp/user.yaml:ScannerError")

    monkeypatch.setattr(safety, "load_user_config", fake_load_user_config)

    with pytest.raises(ConfigLoadError):
        safety.load_gates()


def test_load_gates_normal_values_unchanged(monkeypatch):
    monkeypatch.setattr(
        safety,
        "load_user_config",
        lambda *, strict=False: {
            "safety": {
                "min_order_notional": "12.5",
                "max_trades_per_day": "3",
                "max_daily_loss": "42.0",
                "prefer_journal_pnl": True,
            }
        },
    )

    gates = safety.load_gates()

    assert gates == safety.SafetyGates(
        min_order_notional=12.5,
        max_trades_per_day=3,
        max_daily_loss=42.0,
        prefer_journal_pnl=True,
    )
