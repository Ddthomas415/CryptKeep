from __future__ import annotations

from scripts import bot_status, start_bot, stop_bot


def test_start_bot_converges_paper_mode_without_live_consumer(monkeypatch):
    applied: list[dict[str, object]] = []
    written: list[dict[str, object]] = []

    monkeypatch.setattr(start_bot.rbr, "load_trading_cfg", lambda: {"cfg": True})
    monkeypatch.setattr(
        start_bot.rbr,
        "desired_state",
        lambda cfg: {
            "mode": "paper",
            "live_enabled": False,
            "venue": "coinbase",
            "symbols": ["BTC/USD", "ETH/USD"],
            "with_reconcile": False,
        },
    )
    monkeypatch.setattr(
        start_bot.rbr,
        "apply_state",
        lambda state, *, force_restart=False: applied.append({"state": dict(state), "force_restart": force_restart}) or {"ok": True, "started": [], "stopped": [], "status": {}},
    )
    monkeypatch.setattr(start_bot.rbr, "state_signature", lambda state: "sig-paper")
    monkeypatch.setattr(start_bot.rbr, "write_status", lambda payload: written.append(dict(payload)))
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py"])

    assert start_bot.main() == 0
    assert applied == [
        {
            "state": {
                "mode": "paper",
                "live_enabled": False,
                "venue": "coinbase",
                "symbols": ["BTC/USD", "ETH/USD"],
                "with_reconcile": False,
            },
            "force_restart": False,
        }
    ]
    assert written[-1]["status"] == "converged"
    assert written[-1]["one_shot"] is True
    assert written[-1]["signature"] == "sig-paper"
    assert written[-1]["state"]["with_reconcile"] is False


def test_start_bot_with_reconcile_overrides_state(monkeypatch):
    applied: list[dict[str, object]] = []

    monkeypatch.setattr(start_bot.rbr, "load_trading_cfg", lambda: {"cfg": True})
    monkeypatch.setattr(
        start_bot.rbr,
        "desired_state",
        lambda cfg: {
            "mode": "paper",
            "live_enabled": False,
            "venue": "coinbase",
            "symbols": ["BTC/USD", "SOL/USD"],
            "with_reconcile": False,
        },
    )
    monkeypatch.setattr(
        start_bot.rbr,
        "apply_state",
        lambda state, *, force_restart=False: applied.append({"state": dict(state), "force_restart": force_restart}) or {"ok": True, "started": [], "stopped": [], "status": {}},
    )
    monkeypatch.setattr(start_bot.rbr, "state_signature", lambda state: "sig-reconcile")
    monkeypatch.setattr(start_bot.rbr, "write_status", lambda payload: None)
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py", "--with_reconcile"])

    assert start_bot.main() == 0
    assert applied == [
        {
            "state": {
                "mode": "paper",
                "live_enabled": False,
                "venue": "coinbase",
                "symbols": ["BTC/USD", "SOL/USD"],
                "with_reconcile": True,
            },
            "force_restart": False,
        }
    ]


def test_start_bot_writes_blocked_status_on_invalid_config(monkeypatch):
    written: list[dict[str, object]] = []

    monkeypatch.setattr(start_bot.rbr, "load_trading_cfg", lambda: {"cfg": True})
    monkeypatch.setattr(
        start_bot.rbr,
        "desired_state",
        lambda cfg: (_ for _ in ()).throw(RuntimeError("CBP_CONFIG_REQUIRED:missing_config:pipeline.exchange_id")),
    )
    monkeypatch.setattr(start_bot.rbr, "write_status", lambda payload: written.append(dict(payload)))
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py"])

    assert start_bot.main() == 2
    assert written[-1]["status"] == "blocked"
    assert written[-1]["error"] == "CBP_CONFIG_REQUIRED:missing_config:pipeline.exchange_id"


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
