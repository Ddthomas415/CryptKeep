import services.execution.live_arming as mod


def test_live_armed_signal_uses_state_when_env_not_set(monkeypatch):
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("CBP_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_EXECUTION_LIVE_ENABLED", raising=False)

    monkeypatch.setattr(
        mod,
        "get_live_armed_state",
        lambda: {
            "armed": True,
            "writer": "resume_gate",
            "reason": "operator_resume",
            "ts_epoch": 123.0,
        },
    )

    ok, reason = mod.live_armed_signal()

    assert ok is True
    assert reason == "state:resume_gate"


def test_live_armed_signal_env_still_has_priority(monkeypatch):
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "YES")
    monkeypatch.setattr(
        mod,
        "get_live_armed_state",
        lambda: {
            "armed": False,
            "writer": "resume_gate",
            "reason": "operator_resume",
            "ts_epoch": 123.0,
        },
    )

    ok, reason = mod.live_armed_signal()

    assert ok is True
    assert reason == "env:CBP_EXECUTION_ARMED"
