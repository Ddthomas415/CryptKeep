from __future__ import annotations

from services.execution import live_arming as la


def test_is_live_enabled_accepts_only_canonical_shape():
    assert la.is_live_enabled({"live": {"enabled": True}}) is False
    assert la.is_live_enabled({"live_trading": {"enabled": True}}) is False
    assert la.is_live_enabled({"risk": {"enable_live": True}}) is False
    assert la.is_live_enabled({"execution": {"live_enabled": True}}) is True
    assert la.is_live_enabled({"live": {"enabled": "false"}}) is False


def test_set_live_enabled_writes_only_canonical_shape():
    cfg = la.set_live_enabled({"risk": {"live": {"max_trades_per_day": 5}}}, True)

    assert cfg["execution"]["live_enabled"] is True
    assert cfg["risk"]["live"]["max_trades_per_day"] == 5

    cfg = la.set_live_enabled(cfg, False)

    assert cfg["execution"]["live_enabled"] is False


def test_live_enabled_and_armed_requires_enable_and_arm_signal(monkeypatch):
    monkeypatch.setattr(la, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    for name in ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED", "CBP_EXECUTION_LIVE_ENABLED", "ENABLE_LIVE_TRADING", "LIVE_TRADING", "CBP_LIVE_ARMED"):
        monkeypatch.delenv(name, raising=False)

    armed, reason = la.live_enabled_and_armed()
    assert armed is False
    assert reason == "live_not_armed"

    monkeypatch.setenv("CBP_EXECUTION_ARMED", "YES")
    armed, reason = la.live_enabled_and_armed()
    assert armed is True
    assert reason == "env:CBP_EXECUTION_ARMED"



def test_live_risk_cfg_reads_nested_and_legacy_fallbacks(monkeypatch):
    monkeypatch.setattr(
        la,
        "load_user_yaml",
        lambda: {
            "risk": {
                "live": {
                    "max_trades_per_day": 7,
                    "max_daily_notional_quote": 1250.5,
                },
                "min_order_usd": 15.0,
            }
        },
    )

    cfg = la.live_risk_cfg()

    assert cfg == {
        "max_trades_per_day": 7,
        "max_daily_notional_quote": 1250.5,
        "min_order_notional_quote": 15.0,
    }

def test_live_enabled_and_armed_rejects_enable_live_trading_as_runtime_arm_signal(monkeypatch):
    monkeypatch.setattr(la, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    for name in ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED", "CBP_EXECUTION_LIVE_ENABLED", "ENABLE_LIVE_TRADING", "LIVE_TRADING", "CBP_LIVE_ARMED"):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("ENABLE_LIVE_TRADING", "1")
    armed, reason = la.live_enabled_and_armed()

    assert armed is False
    assert reason == "live_not_armed"


def test_live_enabled_and_armed_rejects_persisted_arm_state_without_boundary_env(monkeypatch):
    monkeypatch.setattr(la, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    for name in ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED", "CBP_EXECUTION_LIVE_ENABLED", "ENABLE_LIVE_TRADING", "LIVE_TRADING", "CBP_LIVE_ARMED"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        la,
        "get_live_armed_state",
        lambda: {"armed": True, "writer": "resume_gate", "reason": "resume", "ts_epoch": 1.0},
    )

    armed, reason = la.live_enabled_and_armed()

    assert armed is False
    assert reason == "live_not_armed"
