from __future__ import annotations

from services.admin import live_enable_wizard as lew
from services.admin import system_guard
from services.execution import live_reconciler as lr
from services.process import watchdog


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


def test_system_guard_shared_file_flow_across_modules(monkeypatch, tmp_path):
    guard_path = tmp_path / "runtime" / "system_guard.json"
    monkeypatch.setattr(system_guard, "GUARD_PATH", guard_path)

    monkeypatch.delenv("CBP_LIVE_ARMED", raising=False)
    monkeypatch.setattr(lew, "_log_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(lew, "load_user_yaml", lambda: {"execution": {"live_enabled": False}})
    monkeypatch.setattr(lew, "save_user_yaml", lambda cfg: (True, "Saved"))
    monkeypatch.setattr(lew, "live_enabled_and_armed", lambda: (True, "env:CBP_LIVE_ARMED"))

    enabled = lew.enable_live()

    assert enabled["ok"] is True
    assert enabled["system_guard"]["state"] == "RUNNING"
    assert system_guard.get_state()["state"] == "RUNNING"

    halted_by_watchdog = watchdog._system_guard_halting("watchdog:heartbeat_stale")

    assert halted_by_watchdog["ok"] is True
    assert halted_by_watchdog["system_guard"]["state"] == "HALTING"
    assert system_guard.get_state()["state"] == "HALTING"

    class _EmptyQueue:
        def list_intents(self, *, limit: int = 60, status: str):
            assert status == "submitted"
            return []

    promoted = lr._maybe_promote_system_guard_halted(_EmptyQueue(), system_guard.get_state(fail_closed=False))

    assert promoted["state"] == "HALTED"
    assert promoted["writer"] == "live_reconciler"
    assert promoted["reason"] == "cleanup_complete"
    assert system_guard.get_state()["state"] == "HALTED"
