from __future__ import annotations

from services.execution import strategy_runner


def test_run_once_hold_does_not_record_trade(monkeypatch):
    calls = {"can_trade": 0, "record_trade": 0, "check_orderbook": 0}

    def _fake_can_trade(*args, **kwargs):
        calls["can_trade"] += 1
        return type("T", (), {"ok": True, "wait_seconds": 0.0})()

    def _fake_record_trade(*args, **kwargs):
        calls["record_trade"] += 1

    def _fake_check_orderbook(*args, **kwargs):
        calls["check_orderbook"] += 1
        return {"ok": True}

    monkeypatch.setattr(strategy_runner, "can_trade", _fake_can_trade)
    monkeypatch.setattr(strategy_runner, "record_trade", _fake_record_trade)
    monkeypatch.setattr(strategy_runner, "check_orderbook", _fake_check_orderbook)

    strategy_runner.run_once()

    assert calls["can_trade"] == 0
    assert calls["record_trade"] == 0
    assert calls["check_orderbook"] == 0
