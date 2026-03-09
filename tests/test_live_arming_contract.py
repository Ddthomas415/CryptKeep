from __future__ import annotations

from services.execution import live_arming as la


def test_is_live_enabled_accepts_current_and_legacy_shapes():
    assert la.is_live_enabled({"live": {"enabled": True}}) is True
    assert la.is_live_enabled({"live_trading": {"enabled": True}}) is True
    assert la.is_live_enabled({"risk": {"enable_live": True}}) is True
    assert la.is_live_enabled({"execution": {"live_enabled": True}}) is True
    assert la.is_live_enabled({"live": {"enabled": "false"}}) is False


def test_set_live_enabled_normalizes_all_compatibility_shapes():
    cfg = la.set_live_enabled({"risk": {"live": {"max_trades_per_day": 5}}}, True)

    assert cfg["live"]["enabled"] is True
    assert cfg["live_trading"]["enabled"] is True
    assert cfg["risk"]["enable_live"] is True
    assert cfg["execution"]["live_enabled"] is True
    assert cfg["risk"]["live"]["max_trades_per_day"] == 5

    cfg = la.set_live_enabled(cfg, False)

    assert cfg["live"]["enabled"] is False
    assert cfg["live_trading"]["enabled"] is False
    assert cfg["risk"]["enable_live"] is False
    assert cfg["execution"]["live_enabled"] is False


def test_live_enabled_and_armed_requires_enable_and_arm_signal(monkeypatch):
    monkeypatch.setattr(la, "load_user_yaml", lambda: {"live": {"enabled": True}})
    for name in ("CBP_LIVE_ARMED", "CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED", "ENABLE_LIVE_TRADING", "LIVE_TRADING"):
        monkeypatch.delenv(name, raising=False)

    armed, reason = la.live_enabled_and_armed()
    assert armed is False
    assert reason == "live_not_armed"

    monkeypatch.setenv("CBP_LIVE_ARMED", "YES")
    armed, reason = la.live_enabled_and_armed()
    assert armed is True
    assert reason == "env:CBP_LIVE_ARMED"



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
