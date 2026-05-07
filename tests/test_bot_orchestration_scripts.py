from __future__ import annotations

from scripts import bot_status, start_bot, stop_bot


def test_start_bot_starts_ops_risk_gate_by_default(monkeypatch):
    started: list[str] = []
    cmds: dict[str, list[str]] = {}
    envs: dict[str, dict[str, str] | None] = {}
    status_calls: list[list[str]] = []

    def _start_process(name, cmd, *, env=None):
        started.append(str(name))
        cmds[str(name)] = list(cmd)
        envs[str(name)] = dict(env) if env else None
        return {"ok": True, "name": name}

    monkeypatch.setattr(
        start_bot,
        "start_process",
        _start_process,
    )
    monkeypatch.setattr(
        start_bot,
        "_service_envs",
        lambda: {
            "pipeline": {"CBP_SYMBOLS": "BTC/USD,ETH/USD"},
            "executor": {"CBP_SYMBOLS": "BTC/USD,ETH/USD"},
            "intent_consumer": {"CBP_SYMBOLS": "BTC/USD,ETH/USD"},
        },
    )
    monkeypatch.setattr(start_bot, "status", lambda names: status_calls.append(list(names)) or {})
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py"])

    assert start_bot.main() == 0
    assert started == ["pipeline", "executor", "intent_consumer", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor"]
    assert cmds["pipeline"] == [start_bot.sys.executable, "scripts/run_pipeline_safe.py"]
    assert cmds["executor"] == [start_bot.sys.executable, "scripts/run_intent_executor_safe.py"]
    assert cmds["intent_consumer"] == [start_bot.sys.executable, "scripts/run_intent_consumer_safe.py", "run"]
    assert cmds["ai_alert_monitor"] == [start_bot.sys.executable, "scripts/run_ai_alert_monitor.py"]
    assert envs["pipeline"] == {"CBP_SYMBOLS": "BTC/USD,ETH/USD"}
    assert envs["executor"] == {"CBP_SYMBOLS": "BTC/USD,ETH/USD"}
    assert envs["intent_consumer"] == {"CBP_SYMBOLS": "BTC/USD,ETH/USD"}
    assert envs["ops_signal_adapter"] is None
    assert status_calls == [start_bot.ALL_SERVICES]


def test_start_bot_with_reconcile_starts_reconciler(monkeypatch):
    started: list[str] = []
    cmds: dict[str, list[str]] = {}
    envs: dict[str, dict[str, str] | None] = {}

    def _start_process(name, cmd, *, env=None):
        started.append(str(name))
        cmds[str(name)] = list(cmd)
        envs[str(name)] = dict(env) if env else None
        return {"ok": True, "name": name}

    monkeypatch.setattr(
        start_bot,
        "start_process",
        _start_process,
    )
    monkeypatch.setattr(
        start_bot,
        "_service_envs",
        lambda: {
            "pipeline": {"CBP_SYMBOLS": "BTC/USD,SOL/USD"},
            "executor": {"CBP_SYMBOLS": "BTC/USD,SOL/USD"},
            "intent_consumer": {"CBP_SYMBOLS": "BTC/USD,SOL/USD"},
            "reconciler": {"CBP_SYMBOLS": "BTC/USD,SOL/USD"},
        },
    )
    monkeypatch.setattr(start_bot, "status", lambda _names: {})
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py", "--with_reconcile"])

    assert start_bot.main() == 0
    assert started == ["pipeline", "executor", "intent_consumer", "ops_signal_adapter", "ops_risk_gate", "ai_alert_monitor", "reconciler"]
    assert cmds["intent_consumer"] == [start_bot.sys.executable, "scripts/run_intent_consumer_safe.py", "run"]
    assert cmds["reconciler"] == [start_bot.sys.executable, "scripts/run_live_reconciler_safe.py", "run"]
    assert envs["reconciler"] == {"CBP_SYMBOLS": "BTC/USD,SOL/USD"}


def test_stop_bot_defaults_to_all_services(monkeypatch):
    stopped: list[str] = []
    status_calls: list[list[str]] = []

    monkeypatch.setattr(stop_bot, "stop_process", lambda name: stopped.append(str(name)) or {"ok": True, "name": name})
    monkeypatch.setattr(stop_bot, "status", lambda names: status_calls.append(list(names)) or {})
    monkeypatch.setattr(stop_bot.sys, "argv", ["stop_bot.py"])

    assert stop_bot.main() == 0
    assert stopped == stop_bot.ALL_SERVICES
    assert status_calls == [stop_bot.ALL_SERVICES]


def test_stop_bot_can_target_intent_consumer_only(monkeypatch):
    stopped: list[str] = []

    monkeypatch.setattr(stop_bot, "stop_process", lambda name: stopped.append(str(name)) or {"ok": True, "name": name})
    monkeypatch.setattr(stop_bot, "status", lambda _names: {})
    monkeypatch.setattr(stop_bot.sys, "argv", ["stop_bot.py", "--intent_consumer"])

    assert stop_bot.main() == 0
    assert stopped == ["intent_consumer"]


def test_stop_bot_can_target_ops_risk_gate_only(monkeypatch):
    stopped: list[str] = []

    monkeypatch.setattr(stop_bot, "stop_process", lambda name: stopped.append(str(name)) or {"ok": True, "name": name})
    monkeypatch.setattr(stop_bot, "status", lambda _names: {})
    monkeypatch.setattr(stop_bot.sys, "argv", ["stop_bot.py", "--ops_risk_gate"])

    assert stop_bot.main() == 0
    assert stopped == ["ops_risk_gate"]


def test_stop_bot_can_target_ops_signal_adapter_only(monkeypatch):
    stopped: list[str] = []

    monkeypatch.setattr(stop_bot, "stop_process", lambda name: stopped.append(str(name)) or {"ok": True, "name": name})
    monkeypatch.setattr(stop_bot, "status", lambda _names: {})
    monkeypatch.setattr(stop_bot.sys, "argv", ["stop_bot.py", "--ops_signal_adapter"])

    assert stop_bot.main() == 0
    assert stopped == ["ops_signal_adapter"]


def test_stop_bot_can_target_ai_alert_monitor_only(monkeypatch):
    stopped: list[str] = []

    monkeypatch.setattr(stop_bot, "stop_process", lambda name: stopped.append(str(name)) or {"ok": True, "name": name})
    monkeypatch.setattr(stop_bot, "status", lambda _names: {})
    monkeypatch.setattr(stop_bot.sys, "argv", ["stop_bot.py", "--ai_alert_monitor"])

    assert stop_bot.main() == 0
    assert stopped == ["ai_alert_monitor"]


def test_bot_status_includes_ops_risk_gate(monkeypatch):
    status_calls: list[list[str]] = []

    monkeypatch.setattr(bot_status, "status", lambda names: status_calls.append(list(names)) or {})

    assert bot_status.main() == 0
    assert status_calls == [bot_status.ALL_SERVICES]
