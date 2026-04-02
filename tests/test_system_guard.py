from __future__ import annotations

from services.admin import system_guard


def test_system_guard_get_state_fail_closed_when_missing(monkeypatch, tmp_path):
    guard_path = tmp_path / "runtime" / "system_guard.json"
    monkeypatch.setattr(system_guard, "GUARD_PATH", guard_path)

    state = system_guard.get_state(fail_closed=True)

    assert state["state"] == "HALTED"
    assert state["reason"] == "missing"
    assert guard_path.exists() is False


def test_system_guard_set_state_writes_and_increments_epoch(monkeypatch, tmp_path):
    guard_path = tmp_path / "runtime" / "system_guard.json"
    monkeypatch.setattr(system_guard, "GUARD_PATH", guard_path)

    first = system_guard.set_state("RUNNING", writer="operator", reason="boot")
    second = system_guard.set_state("HALTING", writer="watchdog", reason="stale")

    assert first["epoch"] == 1
    assert second["epoch"] == 2
    assert system_guard.get_state()["state"] == "HALTING"
    assert system_guard.get_state()["writer"] == "watchdog"


def test_system_guard_get_state_fail_closed_when_invalid(monkeypatch, tmp_path):
    guard_path = tmp_path / "runtime" / "system_guard.json"
    guard_path.parent.mkdir(parents=True, exist_ok=True)
    guard_path.write_text("{not json}\n", encoding="utf-8")
    monkeypatch.setattr(system_guard, "GUARD_PATH", guard_path)

    state = system_guard.get_state(fail_closed=True)

    assert state["state"] == "HALTED"
    assert state["reason"] == "invalid"
