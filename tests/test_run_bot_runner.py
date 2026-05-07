from __future__ import annotations

import threading

import pytest

from scripts import run_bot_runner as rbr


def test_load_trading_cfg_uses_runtime_trading_loader(monkeypatch):
    monkeypatch.setattr(rbr, "load_runtime_trading_config", lambda path="config/trading.yaml": {"loaded_from": path})

    cfg = rbr.load_trading_cfg()

    assert cfg == {"loaded_from": "config/trading.yaml"}


def test_desired_state_live_enables_reconcile():
    cfg = {
        "execution": {"executor_mode": "live", "live_enabled": True},
        "live": {"enabled": False, "exchange_id": "binance"},
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
    cfg = {
        "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase", "symbols": ["BTC/USD", "ETH/USD"]},
        "live": {"exchange_id": "coinbase"},
        "pipeline": {"exchange_id": "coinbase", "symbols": ["BTC/USD", "ETH/USD"]},
        "symbols": "btc/usd",
    }
    st = rbr.desired_state(cfg)
    assert st["mode"] == "paper"
    assert st["with_reconcile"] is False
    assert st["venue"] == "coinbase"
    assert st["symbols"] == ["BTC/USD", "ETH/USD"]
    assert rbr.desired_services(st) == ["pipeline", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor", "executor"]


def test_command_map_uses_safe_wrappers_for_managed_services():
    cmds = rbr.command_map()
    assert cmds["pipeline"] == [rbr.sys.executable, "scripts/run_pipeline_safe.py"]
    assert cmds["intent_consumer"] == [rbr.sys.executable, "scripts/run_intent_consumer_safe.py", "run"]
    assert cmds["reconciler"] == [rbr.sys.executable, "scripts/run_live_reconciler_safe.py", "run"]
    assert cmds["ai_alert_monitor"] == [rbr.sys.executable, "scripts/run_ai_alert_monitor.py"]


def test_desired_state_requires_explicit_exchange_id():
    cfg = {"execution": {"executor_mode": "paper", "live_enabled": False}, "symbols": ["BTC/USD"]}

    with pytest.raises(RuntimeError) as exc:
        rbr.desired_state(cfg)
    assert str(exc.value) == "CBP_CONFIG_REQUIRED:missing_config:pipeline.exchange_id"


def test_desired_state_paper_prefers_actual_paper_venue_over_live_exchange_id():
    cfg = {
        "mode": "paper",
        "symbols": ["BTC/USD"],
        "live": {"exchange_id": "binance", "enabled": False},
        "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
        "pipeline": {"exchange_id": "coinbase"},
    }

    st = rbr.desired_state(cfg)

    assert st["venue"] == "coinbase"


def test_desired_state_paper_rejects_conflicting_execution_and_pipeline_venues():
    cfg = {
        "mode": "paper",
        "symbols": ["BTC/USD"],
        "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
        "pipeline": {"exchange_id": "binance"},
    }

    with pytest.raises(RuntimeError) as exc:
        rbr.desired_state(cfg)

    assert str(exc.value) == "CBP_CONFIG_REQUIRED:conflicting_config:execution.venue_vs_pipeline.exchange_id"


def test_desired_state_requires_explicit_symbols():
    cfg = {
        "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
        "live": {"exchange_id": "coinbase"},
        "pipeline": {"exchange_id": "coinbase"},
    }

    with pytest.raises(RuntimeError) as exc:
        rbr.desired_state(cfg)
    assert str(exc.value) == r"CBP_CONFIG_REQUIRED:missing_config:symbols[0]"


def test_desired_state_prefers_supervised_symbol_lists_over_root_symbols():
    cfg = {
        "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase", "symbols": ["BTC/USD", "ETH/USD"]},
        "live": {"exchange_id": "coinbase"},
        "pipeline": {"exchange_id": "coinbase", "symbols": ["BTC/USD", "ETH/USD"]},
        "symbols": ["BTC/USDT", "ETH/USDT"],
    }

    st = rbr.desired_state(cfg)

    assert st["symbols"] == ["BTC/USD", "ETH/USD"]


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
    assert started == rbr.desired_services(state)


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
    assert stopped == rbr.desired_services(state)
    assert started == rbr.desired_services(state)


def test_run_loop_once_converges_without_shutdown(monkeypatch):
    guard_calls: list[dict[str, str]] = []
    stopped: list[str] = []
    statuses: list[dict[str, object]] = []

    monkeypatch.setattr(
        rbr,
        "load_trading_cfg",
        lambda _path="config/trading.yaml": {
            "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
            "live": {"exchange_id": "coinbase"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["BTC/USD"],
        },
    )
    monkeypatch.setattr(
        rbr,
        "apply_state",
        lambda state, *, force_restart=False: {
            "ok": True,
            "force_restart": force_restart,
            "state": state,
            "started": [{"name": "pipeline"}],
            "stopped": [],
            "status": {},
        },
    )
    monkeypatch.setattr(
        rbr,
        "request_system_guard_halt",
        lambda **kwargs: guard_calls.append(dict(kwargs)) or {"ok": True, "payload": {"state": "HALTING"}},
    )
    monkeypatch.setattr(rbr, "stop_process", lambda name: stopped.append(name) or {"ok": True, "name": name})
    monkeypatch.setattr(rbr, "write_status", lambda payload: statuses.append(dict(payload)))

    assert rbr.run_loop(once=True) == 0
    assert guard_calls == []
    assert stopped == []
    assert statuses[-1]["status"] == "converged"
    assert statuses[-1]["one_shot"] is True


class _StopAfterOneWait:
    def __init__(self):
        self._event = threading.Event()
        self.wait_calls = 0

    def clear(self) -> None:
        self._event.clear()
        self.wait_calls = 0

    def is_set(self) -> bool:
        return self._event.is_set()

    def set(self) -> None:
        self._event.set()

    def wait(self, _timeout: float) -> bool:
        self.wait_calls += 1
        self._event.set()
        return True


def test_run_loop_shutdown_requests_system_guard_before_stopping(monkeypatch):
    guard_calls: list[dict[str, str]] = []
    stopped: list[str] = []
    statuses: list[dict[str, object]] = []

    monkeypatch.setattr(
        rbr,
        "load_trading_cfg",
        lambda _path="config/trading.yaml": {
            "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
            "live": {"exchange_id": "coinbase"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["BTC/USD"],
        },
    )
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
    monkeypatch.setattr(rbr, "STOP_EVENT", _StopAfterOneWait())

    assert rbr.run_loop(once=False) == 0
    assert guard_calls == [{"writer": "bot_runner", "reason": "bot_runner_shutdown"}]
    assert stopped == ["executor", "reconciler"]
    assert statuses[-1]["status"] == "stopped"
    assert statuses[-1]["system_guard"]["ok"] is True


def test_run_loop_shutdown_surfaces_guard_failure_but_still_stops(monkeypatch):
    stopped: list[str] = []
    statuses: list[dict[str, object]] = []

    monkeypatch.setattr(
        rbr,
        "load_trading_cfg",
        lambda _path="config/trading.yaml": {
            "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
            "live": {"exchange_id": "coinbase"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["BTC/USD"],
        },
    )
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
    monkeypatch.setattr(rbr, "STOP_EVENT", _StopAfterOneWait())

    assert rbr.run_loop(once=False) == 0
    assert stopped == ["executor", "reconciler"]
    assert statuses[-1]["ok"] is False
    assert statuses[-1]["system_guard"]["reason"] == "system_guard_write_failed:RuntimeError"


def test_run_loop_blocks_on_missing_required_runtime_config(monkeypatch):
    statuses: list[dict[str, object]] = []

    monkeypatch.setattr(rbr, "load_trading_cfg", lambda _path="config/trading.yaml": {})
    monkeypatch.setattr(rbr, "apply_state", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not apply state")))
    monkeypatch.setattr(rbr, "write_status", lambda payload: statuses.append(dict(payload)))

    assert rbr.run_loop(once=True) == 2
    assert statuses[-1]["status"] == "blocked"
    assert statuses[-1]["error"] == "CBP_CONFIG_REQUIRED:missing_or_invalid_config:execution.executor_mode"
