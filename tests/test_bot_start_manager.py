from __future__ import annotations

from services.bot import start_manager as sm


def test_decide_start_live_accepts_risk_live_shape(monkeypatch):
    monkeypatch.setattr(sm, "_ui_gate", lambda _cfg: (True, "OK", []))

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
    monkeypatch.setattr(
        sm,
        "start_process",
        lambda *, mode, module: captured.update({"mode": mode, "module": module}) or sm.ProcStatus(True, 222, mode, 1, module, "/tmp/live.log"),
    )

    decision, status = sm.start("live")

    assert decision.ok is True
    assert captured == {"mode": "live", "module": "services.bot.cli_live"}
    assert status.mode == "live"
