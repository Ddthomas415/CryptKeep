from __future__ import annotations

from services.bot import start_manager as sm


def test_load_cfg_uses_runtime_trading_loader(monkeypatch):
    monkeypatch.setattr(sm, "load_runtime_trading_config", lambda path="config/trading.yaml": {"loaded_from": path})

    cfg = sm._load_cfg()

    assert cfg == {"loaded_from": "config/trading.yaml"}


def test_start_manager_is_marked_compatibility_only():
    assert sm.COMPATIBILITY_ONLY is True
    assert sm.CANONICAL_CONTROL_SURFACE == {
        "start": "scripts/start_bot.py",
        "stop": "scripts/stop_bot.py",
        "status": "scripts/bot_status.py",
    }


def test_decide_start_live_accepts_risk_live_shape(monkeypatch):
    monkeypatch.setattr(sm, "_ui_gate", lambda _cfg: (True, "OK", []))
    monkeypatch.setattr(sm, "is_live_enabled", lambda cfg=None: True)

    decision = sm.decide_start(
        "live",
        {
            "live": {"sandbox": True},
            "risk": {
                "live": {
                    "max_daily_loss_usd": 25,
                    "max_notional_per_trade_usd": 25,
                    "max_position_notional_usd": 50,
                }
            },
        },
    )

    assert decision.ok is True
    assert decision.status == "OK"


def test_decide_start_live_blocks_when_live_enablement_is_false(monkeypatch):
    monkeypatch.setattr(sm, "is_live_enabled", lambda cfg=None: False)

    decision = sm.decide_start(
        "live",
        {
            "live": {"sandbox": True},
            "execution": {"live_enabled": False},
        },
    )

    assert decision.ok is False
    assert decision.status == "BLOCK"
    assert decision.reasons == ["execution.live_enabled is false"]


def test_start_routes_paper_to_cli_paper(monkeypatch):
    captured: dict[str, str] = {}

    monkeypatch.setattr(sm, "_load_cfg", lambda: {})
    monkeypatch.setattr(
        sm,
        "start_process",
        lambda *, mode, module: captured.update({"mode": mode, "module": module}) or sm.ProcStatus(True, 111, mode, 1, module, "/tmp/paper.log"),
    )

    decision, status = sm.start("paper")

    assert decision.ok is True
    assert captured == {"mode": "paper", "module": "services.bot.cli_paper"}
    assert status.mode == "paper"


def test_start_routes_live_to_cli_live(monkeypatch):
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        sm,
        "_load_cfg",
        lambda: {
            "live": {"sandbox": True},
            "risk": {
                "live": {
                    "max_daily_loss_usd": 25,
                    "max_notional_per_trade_usd": 25,
                    "max_position_notional_usd": 50,
                }
            },
        },
    )
    monkeypatch.setattr(sm, "_ui_gate", lambda _cfg: (True, "OK", []))
    monkeypatch.setattr(sm, "is_live_enabled", lambda cfg=None: True)
    monkeypatch.setattr(
        sm,
        "start_process",
        lambda *, mode, module: captured.update({"mode": mode, "module": module}) or sm.ProcStatus(True, 222, mode, 1, module, "/tmp/live.log"),
    )

    decision, status = sm.start("live")

    assert decision.ok is True
    assert captured == {"mode": "live", "module": "services.bot.cli_live"}
    assert status.mode == "live"


def test_start_does_not_launch_live_process_when_live_enablement_is_false(monkeypatch):
    launched = {"called": False}

    monkeypatch.setattr(
        sm,
        "_load_cfg",
        lambda: {
            "live": {"sandbox": True},
            "execution": {"live_enabled": False},
        },
    )
    monkeypatch.setattr(sm, "is_live_enabled", lambda cfg=None: False)
    monkeypatch.setattr(sm, "start_process", lambda **kwargs: launched.__setitem__("called", True))
    monkeypatch.setattr(sm, "read_status", lambda: sm.ProcStatus(False, None, "paper", 0, "", ""))

    decision, status = sm.start("live")

    assert decision.ok is False
    assert decision.reasons == ["execution.live_enabled is false"]
    assert launched["called"] is False
    assert status.running is False
