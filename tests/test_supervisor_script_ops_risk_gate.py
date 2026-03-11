from __future__ import annotations

from scripts import supervisor as supervisor_script


def test_supervisor_script_start_forwards_risk_gate_default(monkeypatch):
    calls: dict[str, object] = {}

    monkeypatch.setattr(
        supervisor_script,
        "start",
        lambda **kwargs: calls.update(kwargs) or {"ok": True},
    )
    monkeypatch.setattr(supervisor_script, "stop", lambda **kwargs: {"ok": True, "kwargs": kwargs})
    monkeypatch.setattr(supervisor_script, "status", lambda: {"ok": True})
    monkeypatch.setattr(supervisor_script.sys, "argv", ["supervisor.py", "start", "--no-dashboard"])

    assert supervisor_script.main() == 0
    assert calls.get("start_signal_adapter") is True
    assert calls.get("start_risk_gate") is True


def test_supervisor_script_start_honors_no_risk_gate_flag(monkeypatch):
    calls: dict[str, object] = {}

    monkeypatch.setattr(
        supervisor_script,
        "start",
        lambda **kwargs: calls.update(kwargs) or {"ok": True},
    )
    monkeypatch.setattr(supervisor_script, "stop", lambda **kwargs: {"ok": True, "kwargs": kwargs})
    monkeypatch.setattr(supervisor_script, "status", lambda: {"ok": True})
    monkeypatch.setattr(
        supervisor_script.sys,
        "argv",
        ["supervisor.py", "start", "--no-dashboard", "--no-risk-gate"],
    )

    assert supervisor_script.main() == 0
    assert calls.get("start_risk_gate") is False


def test_supervisor_script_stop_honors_no_risk_gate_flag(monkeypatch):
    calls: dict[str, object] = {}

    monkeypatch.setattr(supervisor_script, "start", lambda **kwargs: {"ok": True, "kwargs": kwargs})
    monkeypatch.setattr(
        supervisor_script,
        "stop",
        lambda **kwargs: calls.update(kwargs) or {"ok": True},
    )
    monkeypatch.setattr(supervisor_script, "status", lambda: {"ok": True})
    monkeypatch.setattr(supervisor_script.sys, "argv", ["supervisor.py", "stop", "--no-risk-gate"])

    assert supervisor_script.main() == 0
    assert calls.get("stop_risk_gate") is False


def test_supervisor_script_start_honors_no_signal_adapter_flag(monkeypatch):
    calls: dict[str, object] = {}

    monkeypatch.setattr(
        supervisor_script,
        "start",
        lambda **kwargs: calls.update(kwargs) or {"ok": True},
    )
    monkeypatch.setattr(supervisor_script, "stop", lambda **kwargs: {"ok": True, "kwargs": kwargs})
    monkeypatch.setattr(supervisor_script, "status", lambda: {"ok": True})
    monkeypatch.setattr(
        supervisor_script.sys,
        "argv",
        ["supervisor.py", "start", "--no-dashboard", "--no-signal-adapter"],
    )

    assert supervisor_script.main() == 0
    assert calls.get("start_signal_adapter") is False
