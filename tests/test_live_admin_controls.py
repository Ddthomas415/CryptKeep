from __future__ import annotations

import os

from services.admin import kill_switch
from services.admin import live_disable_wizard as ldw
from services.admin import live_enable_wizard as lew



def test_kill_switch_get_state_bootstraps_default_file(monkeypatch, tmp_path):
    kill_path = tmp_path / "runtime" / "kill_switch.json"
    monkeypatch.setattr(kill_switch, "KILL_PATH", kill_path)

    state = kill_switch.get_state()

    assert state["armed"] is True
    assert state["note"] == "default"
    assert kill_path.exists()



def test_live_enable_wizard_normalizes_flags_and_arms_env(monkeypatch):
    saved: dict[str, object] = {}
    guard_calls: list[tuple[str, str, str]] = []

    def _save(cfg):
        saved["cfg"] = cfg
        return True, "Saved"

    monkeypatch.delenv("CBP_LIVE_ARMED", raising=False)
    monkeypatch.setattr(lew, "_log_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(lew, "load_user_yaml", lambda: {"risk": {"live": {"max_trades_per_day": 5}}})
    monkeypatch.setattr(lew, "save_user_yaml", _save)
    monkeypatch.setattr(lew, "live_enabled_and_armed", lambda: (True, "env:CBP_LIVE_ARMED"))
    monkeypatch.setattr(
        lew,
        "set_system_guard_state",
        lambda state, *, writer, reason="": guard_calls.append((state, writer, reason)) or {"state": state, "writer": writer, "reason": reason},
    )

    out = lew.enable_live()

    assert out["ok"] is True
    assert os.environ["CBP_LIVE_ARMED"] == "YES"
    assert saved["cfg"]["live"]["enabled"] is True
    assert saved["cfg"]["live_trading"]["enabled"] is True
    assert saved["cfg"]["risk"]["enable_live"] is True
    assert saved["cfg"]["execution"]["live_enabled"] is True
    assert out["system_guard"]["state"] == "RUNNING"
    assert guard_calls == [("RUNNING", "live_enable_wizard", "enable_live")]



def test_live_disable_wizard_disables_all_live_shapes_and_arms_kill_switch(monkeypatch):
    saved: dict[str, object] = {}
    events: list[tuple[str, str, str, dict | None]] = []
    kill = {"armed": False, "note": "before"}
    cfg_state = {"live": {"enabled": True}, "risk": {"enable_live": True}}

    def _save(cfg, dry_run=False):
        saved["cfg"] = cfg
        saved["dry_run"] = dry_run
        cfg_state.clear()
        cfg_state.update(cfg)
        return True, "Saved"

    def _set_armed(state: bool, note: str = "") -> dict:
        kill.update({"armed": bool(state), "note": str(note)})
        return dict(kill)

    monkeypatch.setattr(ldw, "load_user_yaml", lambda: dict(cfg_state))
    monkeypatch.setattr(ldw, "save_user_yaml", _save)
    monkeypatch.setattr(ldw, "get_kill", lambda: dict(kill))
    monkeypatch.setattr(ldw, "set_armed", _set_armed)
    monkeypatch.setattr(ldw, "run_id", lambda: "run-123")
    monkeypatch.setattr(ldw, "log_event", lambda venue, symbol, event, *, ref_id=None, payload=None: events.append((venue, symbol, event, payload)))

    out = ldw.disable_live_now(note="operator_stop")

    assert out["ok"] is True
    assert saved["dry_run"] is False
    assert saved["cfg"]["live"]["enabled"] is False
    assert saved["cfg"]["live_trading"]["enabled"] is False
    assert saved["cfg"]["risk"]["enable_live"] is False
    assert saved["cfg"]["execution"]["live_enabled"] is False
    assert out["post"]["live_enabled"] is False
    assert out["post"]["kill_switch_armed"] is True
    assert events and events[0][2] == "live_disabled"
    assert events[0][3]["note"] == "operator_stop"


def test_live_enable_wizard_disable_sets_system_guard_halted(monkeypatch):
    saved: dict[str, object] = {}
    guard_calls: list[tuple[str, str, str]] = []

    def _save(cfg):
        saved["cfg"] = cfg
        return True, "Saved"

    monkeypatch.setenv("CBP_LIVE_ARMED", "YES")
    monkeypatch.setattr(lew, "_log_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(lew, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(lew, "save_user_yaml", _save)
    monkeypatch.setattr(lew, "live_enabled_and_armed", lambda: (False, "live_disabled"))
    monkeypatch.setattr(
        lew,
        "set_system_guard_state",
        lambda state, *, writer, reason="": guard_calls.append((state, writer, reason)) or {"state": state, "writer": writer, "reason": reason},
    )

    out = lew.disable_live()

    assert out["ok"] is True
    assert out["armed"] is False
    assert saved["cfg"]["execution"]["live_enabled"] is False
    assert "CBP_LIVE_ARMED" not in os.environ
    assert out["system_guard"]["state"] == "HALTED"
    assert guard_calls == [("HALTED", "live_enable_wizard", "disable_live")]

def test_stop_service_from_pidfile_rejects_unsafe_name():
    from services.admin import service_controls as sc

    out = sc.stop_service_from_pidfile("../bad")

    assert out["ok"] is False
    assert out["error"] == "unsafe_service_name"


def test_stop_service_from_pidfile_rejects_unknown_service(monkeypatch):
    from services.admin import service_controls as sc

    monkeypatch.setattr(
        sc,
        "stop_service_from_pidfile",
        sc.stop_service_from_pidfile,
    )

    out = sc.stop_service_from_pidfile("definitely_unknown_service_name")

    assert out["ok"] is False
    assert out["error"] == "unknown_service_name"


def test_stop_service_from_pidfile_invalid_pid_file_unlinks(monkeypatch, tmp_path):
    from services.admin import health
    from services.admin import service_controls as sc
    from services.admin import watchdog

    pid_dir = tmp_path / "pids"
    pid_dir.mkdir(parents=True, exist_ok=True)
    bad_pf = pid_dir / "market_data_poller.pid"
    bad_pf.write_text("not-an-int", encoding="utf-8")

    monkeypatch.setattr(watchdog, "PID_DIR", pid_dir)
    monkeypatch.setattr(health, "set_health", lambda *args, **kwargs: None)

    out = sc.stop_service_from_pidfile("market_data_poller")

    assert out["ok"] is False
    assert out["error"] == "invalid_pid_file"
    assert out["service"] == "market_data_poller"
    assert not bad_pf.exists()


def test_stop_service_from_pidfile_missing_pid_file_is_ok(monkeypatch, tmp_path):
    from services.admin import watchdog
    from services.admin import service_controls as sc

    pid_dir = tmp_path / "pids"
    pid_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(watchdog, "PID_DIR", pid_dir)

    out = sc.stop_service_from_pidfile("market_data_poller")

    assert out["ok"] is True
    assert out["note"] == "pid_file_missing"
    assert out["service"] == "market_data_poller"

def test_stop_service_from_pidfile_rejects_unknown_dashboard_service_name(monkeypatch, tmp_path):
    from services.admin import service_controls as sc
    from services.admin import watchdog

    pid_dir = tmp_path / "pids"
    pid_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(watchdog, "PID_DIR", pid_dir)

    out = sc.stop_service_from_pidfile("dashboard")

    assert out["ok"] is False
    assert out["error"] == "unknown_service_name"


def test_stop_service_from_pidfile_invalid_service_name_with_slash():
    from services.admin import service_controls as sc

    out = sc.stop_service_from_pidfile("bad/name")

    assert out["ok"] is False
    assert out["error"] == "unsafe_service_name"
