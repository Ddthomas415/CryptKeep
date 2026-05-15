from __future__ import annotations

from scripts import bot_status, start_bot, stop_bot


def test_start_bot_converges_paper_topology(monkeypatch):
    statuses: list[dict[str, object]] = []

    monkeypatch.setattr(
        start_bot.rbr,
        "load_trading_cfg",
        lambda: {
            "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
            "live": {"exchange_id": "coinbase"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["BTC/USD"],
        },
    )
    monkeypatch.setattr(start_bot.rbr, "apply_state", lambda state, *, force_restart=False: {"ok": True, "started": [], "stopped": [], "status": {}, "state": state, "force_restart": force_restart})
    monkeypatch.setattr(start_bot.rbr, "write_status", lambda payload: statuses.append(dict(payload)))
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py"])

    assert start_bot.main() == 0
    assert statuses[-1]["status"] == "converged"
    assert statuses[-1]["one_shot"] is True
    assert statuses[-1]["state"]["mode"] == "paper"


def test_start_bot_with_reconcile_converges_reconciler(monkeypatch):
    statuses: list[dict[str, object]] = []

    monkeypatch.setattr(
        start_bot.rbr,
        "load_trading_cfg",
        lambda: {
            "execution": {"executor_mode": "paper", "live_enabled": False, "venue": "coinbase"},
            "live": {"exchange_id": "coinbase"},
            "pipeline": {"exchange_id": "coinbase"},
            "symbols": ["BTC/USD"],
        },
    )
    monkeypatch.setattr(start_bot.rbr, "apply_state", lambda state, *, force_restart=False: {"ok": True, "started": [], "stopped": [], "status": {}, "state": state, "force_restart": force_restart})
    monkeypatch.setattr(start_bot.rbr, "write_status", lambda payload: statuses.append(dict(payload)))
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py", "--with_reconcile"])

    assert start_bot.main() == 0
    assert statuses[-1]["status"] == "converged"
    assert statuses[-1]["state"]["with_reconcile"] is True


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


def test_bot_status_includes_ai_alert_monitor(monkeypatch):
    monkeypatch.setattr(
        bot_status,
        "canonical_service_status",
        lambda: {name: {"running": name == "ai_alert_monitor", "pid": 42 if name == "ai_alert_monitor" else None} for name in bot_status.ALL_SERVICES},
    )

    assert bot_status.main() == 0
    assert "ai_alert_monitor" in bot_status.ALL_SERVICES
