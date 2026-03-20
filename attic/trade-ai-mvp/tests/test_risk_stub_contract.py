import asyncio

from services.risk_stub import app as risk_app


def test_risk_stub_research_mode_defaults_to_full_stop(monkeypatch):
    monkeypatch.setattr(risk_app.settings, "paper_trading_enabled", False)
    out = asyncio.run(risk_app.evaluate_risk({"asset": "SOL", "mode": "research"}))
    assert out["execution_disabled"] is True
    assert out["approved"] is False
    assert out["paper_approved"] is False
    assert out["gate"] == "FULL_STOP"
    assert "OBSERVE_ONLY" in out["allowed_actions"]


def test_risk_stub_paper_mode_rejected_when_disabled(monkeypatch):
    monkeypatch.setattr(risk_app.settings, "paper_trading_enabled", False)
    out = asyncio.run(risk_app.evaluate_risk({"asset": "SOL", "mode": "paper"}))
    assert out["execution_disabled"] is True
    assert out["approved"] is False
    assert out["paper_approved"] is False
    assert out["gate"] == "FULL_STOP"
    assert out["reason"] == "Paper trading disabled"


def test_risk_stub_paper_mode_allowed_when_enabled(monkeypatch):
    monkeypatch.setattr(risk_app.settings, "paper_trading_enabled", True)
    out = asyncio.run(risk_app.evaluate_risk({"asset": "SOL", "mode": "paper"}))
    assert out["execution_disabled"] is True
    assert out["approved"] is False
    assert out["paper_approved"] is True
    assert out["gate"] == "ALLOW"
    assert "PAPER_SUBMIT" in out["allowed_actions"]


def test_risk_stub_halts_new_exposure_when_notional_exceeded(monkeypatch):
    monkeypatch.setattr(risk_app.settings, "paper_trading_enabled", True)
    monkeypatch.setattr(risk_app.settings, "paper_max_notional_usd", 100.0)
    out = asyncio.run(
        risk_app.evaluate_risk(
            {
                "asset": "SOL",
                "mode": "paper",
                "requested_action": "open_position",
                "proposed_notional_usd": 150.0,
            }
        )
    )
    assert out["gate"] == "HALT_NEW_EXPOSURE"
    assert out["paper_approved"] is False
    assert "PAPER_REDUCE" in out["allowed_actions"]


def test_risk_stub_allows_reduce_when_halt_new_exposure(monkeypatch):
    monkeypatch.setattr(risk_app.settings, "paper_trading_enabled", True)
    monkeypatch.setattr(risk_app.settings, "paper_max_notional_usd", 100.0)
    out = asyncio.run(
        risk_app.evaluate_risk(
            {
                "asset": "SOL",
                "mode": "paper",
                "requested_action": "reduce_position",
                "proposed_notional_usd": 150.0,
            }
        )
    )
    assert out["gate"] == "HALT_NEW_EXPOSURE"
    assert out["paper_approved"] is True
    assert "PAPER_REDUCE" in out["allowed_actions"]


def test_risk_stub_enforces_reduce_only_when_position_limit_hit(monkeypatch):
    monkeypatch.setattr(risk_app.settings, "paper_trading_enabled", True)
    monkeypatch.setattr(risk_app.settings, "paper_max_position_qty", 2.0)
    out = asyncio.run(
        risk_app.evaluate_risk(
            {
                "asset": "SOL",
                "mode": "paper",
                "requested_action": "open_position",
                "position_qty": 2.0,
            }
        )
    )
    assert out["gate"] == "ALLOW_REDUCE_ONLY"
    assert out["paper_approved"] is False
    assert "PAPER_REDUCE" in out["allowed_actions"]


def test_risk_stub_full_stop_on_daily_loss_breach(monkeypatch):
    monkeypatch.setattr(risk_app.settings, "paper_trading_enabled", True)
    monkeypatch.setattr(risk_app.settings, "paper_daily_loss_limit_usd", 100.0)
    out = asyncio.run(
        risk_app.evaluate_risk(
            {
                "asset": "SOL",
                "mode": "paper",
                "requested_action": "reduce_position",
                "daily_pnl": -150.0,
            }
        )
    )
    assert out["gate"] == "FULL_STOP"
    assert out["paper_approved"] is False
