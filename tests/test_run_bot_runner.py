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
    guard_calls: list[dict[str, str]] = []
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
    monkeypatch.setattr(
        rbr,
        "request_system_guard_halt",
        lambda **kwargs: guard_calls.append(dict(kwargs)) or {"ok": True},
    )
    monkeypatch.setattr(rbr, "is_running", lambda _name: True)
    monkeypatch.setattr(rbr, "status", lambda names: {n: {"running": True} for n in names})

    out = rbr.apply_state(state, force_restart=True)
    assert out["ok"] is True
    assert guard_calls == []
    assert stopped == ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "reconciler"]
    assert started == ["pipeline", "executor", "ops_signal_adapter", "ops_risk_gate", "reconciler"]


def test_run_loop_shutdown_requests_system_guard_before_stopping(monkeypatch):
    guard_calls: list[dict[str, str]] = []
    stopped: list[str] = []
    statuses: list[dict[str, object]] = []

    monkeypatch.setattr(rbr, "load_trading_cfg", lambda _path="config/trading.yaml": {"mode": "paper", "live": {"enabled": False}})
    monkeypatch.setattr(
        rbr,
        "apply_state",
        lambda state, *, force_restart=False: {
            "ok": True,
            "force_restart": force_restart,
            "state": state,
            "started": [],
            "stopped": [],
            "status": {},
        },
    )
    monkeypatch.setattr(
        rbr,
        "request_system_guard_halt",
        lambda **kwargs: guard_calls.append(dict(kwargs)) or {"ok": True, "payload": {"state": "HALTING"}},
    )
    monkeypatch.setattr(rbr, "is_running", lambda name: name in {"executor", "reconciler"})
    monkeypatch.setattr(rbr, "stop_process", lambda name: stopped.append(name) or {"ok": True, "name": name})
    monkeypatch.setattr(rbr, "write_status", lambda payload: statuses.append(dict(payload)))

    assert rbr.run_loop(once=True) == 0
    assert guard_calls == [{"writer": "bot_runner", "reason": "bot_runner_shutdown"}]
    assert stopped == ["executor", "reconciler"]
    assert statuses[-1]["status"] == "stopped"
    assert statuses[-1]["system_guard"]["ok"] is True


def test_run_loop_shutdown_surfaces_guard_failure_but_still_stops(monkeypatch):
    stopped: list[str] = []
    statuses: list[dict[str, object]] = []

    monkeypatch.setattr(rbr, "load_trading_cfg", lambda _path="config/trading.yaml": {"mode": "paper", "live": {"enabled": False}})
    monkeypatch.setattr(
        rbr,
        "apply_state",
        lambda state, *, force_restart=False: {
            "ok": True,
            "force_restart": force_restart,
            "state": state,
            "started": [],
            "stopped": [],
            "status": {},
        },
    )
    monkeypatch.setattr(
        rbr,
        "request_system_guard_halt",
        lambda **_kwargs: {"ok": False, "reason": "system_guard_write_failed:RuntimeError"},
    )
    monkeypatch.setattr(rbr, "is_running", lambda name: name in {"executor", "reconciler"})
    monkeypatch.setattr(rbr, "stop_process", lambda name: stopped.append(name) or {"ok": True, "name": name})
    monkeypatch.setattr(rbr, "write_status", lambda payload: statuses.append(dict(payload)))

    assert rbr.run_loop(once=True) == 0
    assert stopped == ["executor", "reconciler"]
    assert statuses[-1]["ok"] is False
    assert statuses[-1]["system_guard"]["reason"] == "system_guard_write_failed:RuntimeError"
