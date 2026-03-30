import os

from services.execution import live_arming


def test_live_enabled_and_armed_accepts_canonical_env(monkeypatch):
    monkeypatch.setattr(
        live_arming,
        "load_user_yaml",
        lambda: {"execution": {"live_enabled": True}},
    )
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")
    monkeypatch.delenv("ENABLE_LIVE_TRADING", raising=False)

    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is True
    assert reason == "env:CBP_EXECUTION_ARMED"


def test_live_enabled_and_armed_accepts_temporary_compat_env(monkeypatch):
    monkeypatch.setattr(
        live_arming,
        "load_user_yaml",
        lambda: {"execution": {"live_enabled": True}},
    )
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.setenv("ENABLE_LIVE_TRADING", "1")

    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is True
    assert reason == "env:ENABLE_LIVE_TRADING"


def test_live_enabled_and_armed_rejects_removed_legacy_envs(monkeypatch):
    monkeypatch.setattr(
        live_arming,
        "load_user_yaml",
        lambda: {"execution": {"live_enabled": True}},
    )
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("ENABLE_LIVE_TRADING", raising=False)
    monkeypatch.setenv("CBP_LIVE_ARMED", "1")
    monkeypatch.setenv("CBP_LIVE_ENABLED", "1")
    monkeypatch.setenv("LIVE_TRADING", "1")

    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is False
    assert reason == "live_not_armed"
