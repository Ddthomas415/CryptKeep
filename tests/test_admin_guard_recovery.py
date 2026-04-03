from __future__ import annotations


def test_safe_mode_recovery_reapplies_disable_when_system_guard_is_stale_running(monkeypatch):
    from services.admin import safe_mode_recovery as smr

    monkeypatch.setattr(smr, "load_user_yaml", lambda: {"safety": {"auto_disable_live_on_start": True}})
    monkeypatch.setattr(
        smr,
        "status",
        lambda: {
            "risk_enable_live": False,
            "kill_switch_armed": True,
            "system_guard": {"state": "RUNNING", "writer": "legacy", "reason": "stale"},
        },
    )
    monkeypatch.setattr(
        smr,
        "disable_live_now",
        lambda note="": {"ok": True, "note": note, "system_guard": {"state": "HALTED"}},
    )

    out = smr.auto_disable_if_needed()

    assert out["ok"] is True
    assert out["did_action"] is True
    assert out["reason"] == "auto_recovery_on_start"
    assert out["result"]["system_guard"]["state"] == "HALTED"


def test_safe_mode_recovery_skips_when_kill_switch_and_system_guard_are_already_safe(monkeypatch):
    from services.admin import safe_mode_recovery as smr

    monkeypatch.setattr(smr, "load_user_yaml", lambda: {"safety": {"auto_disable_live_on_start": True}})
    monkeypatch.setattr(
        smr,
        "status",
        lambda: {
            "risk_enable_live": False,
            "kill_switch_armed": True,
            "system_guard": {"state": "HALTED", "writer": "test", "reason": "ok"},
        },
    )

    out = smr.auto_disable_if_needed()

    assert out["ok"] is True
    assert out["did_action"] is False
    assert out["reason"] == "already_safe"
