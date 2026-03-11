from __future__ import annotations

from scripts import run_bot_runner as rbr


def test_desired_state_live_enables_reconcile():
    cfg = {
        "mode": "live",
        "live": {"enabled": True, "exchange_id": "binance"},
        "symbols": ["eth/usdt"],
    }
    st = rbr.desired_state(cfg)
    assert st["mode"] == "live"
    assert st["live_enabled"] is True
    assert st["venue"] == "binance"
    assert st["symbols"] == ["ETH/USDT"]
    assert st["with_reconcile"] is True
    assert "reconciler" in rbr.desired_services(st)


def test_desired_state_paper_disables_reconcile():
    cfg = {"mode": "paper", "live": {"enabled": False}, "symbols": "btc/usd"}
    st = rbr.desired_state(cfg)
    assert st["mode"] == "paper"
    assert st["with_reconcile"] is False
    assert rbr.desired_services(st) == ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate"]


def test_apply_state_converges_services(monkeypatch):
    state = {"mode": "paper", "live_enabled": False, "venue": "coinbase", "symbols": ["BTC/USD"], "with_reconcile": False}

    started: list[str] = []
    stopped: list[str] = []
    monkeypatch.setattr(
        rbr,
        "start_process",
        lambda name, cmd: started.append(name) or {"ok": True, "name": name, "cmd": cmd},
    )
    monkeypatch.setattr(
        rbr,
        "stop_process",
        lambda name: stopped.append(name) or {"ok": True, "name": name},
    )
    monkeypatch.setattr(rbr, "is_running", lambda name: name == "reconciler")
    monkeypatch.setattr(rbr, "status", lambda names: {n: {"running": n in started} for n in names})

    out = rbr.apply_state(state, force_restart=False)
    assert out["ok"] is True
    assert stopped == ["reconciler"]
    assert started == ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate"]


def test_apply_state_force_restart_restarts_wanted(monkeypatch):
    state = {"mode": "live", "live_enabled": True, "venue": "coinbase", "symbols": ["BTC/USD"], "with_reconcile": True}

    started: list[str] = []
    stopped: list[str] = []
    monkeypatch.setattr(
        rbr,
        "start_process",
        lambda name, cmd: started.append(name) or {"ok": True, "name": name, "cmd": cmd},
    )
    monkeypatch.setattr(
        rbr,
        "stop_process",
        lambda name: stopped.append(name) or {"ok": True, "name": name},
    )
    monkeypatch.setattr(rbr, "is_running", lambda _name: True)
    monkeypatch.setattr(rbr, "status", lambda names: {n: {"running": True} for n in names})

    out = rbr.apply_state(state, force_restart=True)
    assert out["ok"] is True
    assert stopped == ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "reconciler"]
    assert started == ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "reconciler"]
