from services.execution import live_arming


def test_live_enabled_and_armed_accepts_canonical_env(monkeypatch):
    monkeypatch.setattr(
        live_arming,
        "load_user_yaml",
        lambda: {"execution": {"live_enabled": True}},
    )
    for name in ("CBP_LIVE_ARMED", "CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED", "ENABLE_LIVE_TRADING", "LIVE_TRADING"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")

    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is True
    assert reason == "env:CBP_EXECUTION_ARMED"


def test_live_enabled_and_armed_accepts_operator_arm_env(monkeypatch):
    monkeypatch.setattr(
        live_arming,
        "load_user_yaml",
        lambda: {"execution": {"live_enabled": True}},
    )
    for name in ("CBP_LIVE_ARMED", "CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED", "ENABLE_LIVE_TRADING", "LIVE_TRADING"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CBP_LIVE_ARMED", "1")

    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is True
    assert reason == "env:CBP_LIVE_ARMED"


def test_live_enabled_and_armed_accepts_compat_envs(monkeypatch):
    monkeypatch.setattr(
        live_arming,
        "load_user_yaml",
        lambda: {"execution": {"live_enabled": True}},
    )
    for name in ("CBP_LIVE_ARMED", "CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED", "ENABLE_LIVE_TRADING", "LIVE_TRADING"):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("CBP_LIVE_ENABLED", "1")
    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is True
    assert reason == "env:CBP_LIVE_ENABLED"

    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.setenv("ENABLE_LIVE_TRADING", "1")
    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is True
    assert reason == "env:ENABLE_LIVE_TRADING"

    monkeypatch.delenv("ENABLE_LIVE_TRADING", raising=False)
    monkeypatch.setenv("LIVE_TRADING", "1")
    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is True
    assert reason == "env:LIVE_TRADING"


def test_live_enabled_and_armed_rejects_when_no_arming_env_present(monkeypatch):
    monkeypatch.setattr(
        live_arming,
        "load_user_yaml",
        lambda: {"execution": {"live_enabled": True}},
    )
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("ENABLE_LIVE_TRADING", raising=False)
    monkeypatch.delenv("LIVE_TRADING", raising=False)

    ok, reason = live_arming.live_enabled_and_armed()
    assert ok is False
    assert reason == "live_not_armed"
