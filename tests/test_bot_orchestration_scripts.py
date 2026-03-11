from __future__ import annotations

from scripts import bot_status, start_bot, stop_bot


def test_start_bot_starts_ops_risk_gate_by_default(monkeypatch):
    started: list[str] = []
    status_calls: list[list[str]] = []

    monkeypatch.setattr(
        start_bot,
        "start_process",
        lambda name, _cmd: started.append(str(name)) or {"ok": True, "name": name},
    )
    monkeypatch.setattr(start_bot, "status", lambda names: status_calls.append(list(names)) or {})
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py"])

    assert start_bot.main() == 0
    assert started == ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate"]
    assert status_calls == [start_bot.ALL_SERVICES]


def test_start_bot_with_reconcile_starts_reconciler(monkeypatch):
    started: list[str] = []

    monkeypatch.setattr(
        start_bot,
        "start_process",
        lambda name, _cmd: started.append(str(name)) or {"ok": True, "name": name},
    )
    monkeypatch.setattr(start_bot, "status", lambda _names: {})
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py", "--with_reconcile"])

    assert start_bot.main() == 0
    assert started == ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "reconciler"]


def test_stop_bot_defaults_to_all_services(monkeypatch):
    stopped: list[str] = []
    status_calls: list[list[str]] = []

    monkeypatch.setattr(stop_bot, "stop_process", lambda name: stopped.append(str(name)) or {"ok": True, "name": name})
    monkeypatch.setattr(stop_bot, "status", lambda names: status_calls.append(list(names)) or {})
    monkeypatch.setattr(stop_bot.sys, "argv", ["stop_bot.py"])

    assert stop_bot.main() == 0
    assert stopped == stop_bot.ALL_SERVICES
    assert status_calls == [stop_bot.ALL_SERVICES]


def test_stop_bot_can_target_ops_risk_gate_only(monkeypatch):
    stopped: list[str] = []

    monkeypatch.setattr(stop_bot, "stop_process", lambda name: stopped.append(str(name)) or {"ok": True, "name": name})
    monkeypatch.setattr(stop_bot, "status", lambda _names: {})
    monkeypatch.setattr(stop_bot.sys, "argv", ["stop_bot.py", "--ops_risk_gate"])

    assert stop_bot.main() == 0
    assert stopped == ["ops_risk_gate"]


def test_stop_bot_can_target_ops_signal_adapter_only(monkeypatch):
    stopped: list[str] = []

    monkeypatch.setattr(stop_bot, "stop_process", lambda name: stopped.append(str(name)) or {"ok": True, "name": name})
    monkeypatch.setattr(stop_bot, "status", lambda _names: {})
    monkeypatch.setattr(stop_bot.sys, "argv", ["stop_bot.py", "--ops_signal_adapter"])

    assert stop_bot.main() == 0
    assert stopped == ["ops_signal_adapter"]


def test_bot_status_includes_ops_risk_gate(monkeypatch):
    status_calls: list[list[str]] = []

    monkeypatch.setattr(bot_status, "status", lambda names: status_calls.append(list(names)) or {})

    assert bot_status.main() == 0
    assert status_calls == [bot_status.ALL_SERVICES]
