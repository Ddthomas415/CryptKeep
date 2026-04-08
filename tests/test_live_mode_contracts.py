from __future__ import annotations

import os

import pytest

from services.admin import live_guard
from services.execution import intent_executor
from services.preflight import preflight as pf



def test_live_guard_accepts_current_live_config_shape(monkeypatch):
    monkeypatch.setattr(live_guard, "kill_state", lambda: {"armed": False, "note": "manual"})
    monkeypatch.setattr(live_guard, "get_system_guard_state", lambda **_: {"state": "RUNNING", "writer": "test", "reason": "ok"})
    monkeypatch.setattr(live_guard, "load_user_config", lambda: {"live": {"enabled": True}})

    allowed, reason, details = live_guard.live_allowed()

    assert allowed is True
    assert reason == "ok"
    assert details["live_enabled"] is True
    assert details["system_guard"]["state"] == "RUNNING"


def test_live_guard_blocks_when_system_guard_halted(monkeypatch):
    monkeypatch.setattr(live_guard, "kill_state", lambda: {"armed": False, "note": "manual"})
    monkeypatch.setattr(live_guard, "get_system_guard_state", lambda **_: {"state": "HALTED", "writer": "watchdog", "reason": "stale"})
    monkeypatch.setattr(live_guard, "load_user_config", lambda: {"live": {"enabled": True}})

    allowed, reason, details = live_guard.live_allowed()

    assert allowed is False
    assert reason == "system_guard_halted"
    assert details["system_guard"]["state"] == "HALTED"



def test_intent_executor_live_allowed_accepts_current_live_shape(monkeypatch):
    monkeypatch.setattr(intent_executor, "_killswitch_state", lambda: (False, ""))
    ok, reason = intent_executor._live_allowed({"live": {"enabled": True}})

    assert ok is True
    assert reason == "live_allowed"


def test_intent_executor_live_allowed_blocks_on_probe_failure(monkeypatch):
    monkeypatch.setattr(
        intent_executor,
        "_killswitch_state",
        lambda: (True, "services.risk.killswitch.import_failed:ModuleNotFoundError"),
    )

    ok, reason = intent_executor._live_allowed({"live": {"enabled": True}})

    assert ok is False
    assert reason == "services.risk.killswitch.import_failed:ModuleNotFoundError"


def test_intent_executor_live_allowed_blocks_on_cooldown(monkeypatch):
    monkeypatch.setattr(
        intent_executor,
        "_killswitch_state",
        lambda: (True, "services.risk.killswitch.snapshot.cooldown_active"),
    )

    ok, reason = intent_executor._live_allowed({"live": {"enabled": True}})

    assert ok is False
    assert reason == "services.risk.killswitch.snapshot.cooldown_active"


def test_execute_one_blocks_live_intent_before_adapter_on_probe_failure(monkeypatch):
    updates: list[dict[str, object]] = []
    events: list[dict[str, object]] = []

    monkeypatch.setattr(
        intent_executor,
        "_killswitch_state",
        lambda: (True, "services.risk.killswitch.snapshot_failed:RuntimeError"),
    )
    monkeypatch.setattr(
        intent_executor,
        "claim_next_ready",
        lambda venue=None, mode=None: {
            "intent_id": "intent-1",
            "venue": "coinbase",
            "mode": "live",
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "limit",
            "amount": "0.1",
            "price": "100.0",
        },
    )
    monkeypatch.setattr(intent_executor, "update_intent", lambda **kwargs: updates.append(kwargs))
    monkeypatch.setattr(intent_executor, "log_event", lambda **kwargs: events.append(kwargs))
    monkeypatch.setattr(intent_executor, "get_adapter", lambda **kwargs: pytest.fail("adapter should not be reached"))

    out = intent_executor.execute_one({"live": {"enabled": True}})

    assert out["blocked"] is True
    assert out["reason"] == "services.risk.killswitch.snapshot_failed:RuntimeError"
    assert updates == [
        {
            "intent_id": "intent-1",
            "status": "FAILED",
            "last_error": "services.risk.killswitch.snapshot_failed:RuntimeError",
        }
    ]
    assert events[0]["event"] == "blocked"
    assert events[0]["payload"] == {"reason": "services.risk.killswitch.snapshot_failed:RuntimeError"}



def test_preflight_accepts_current_live_enabled_contract(tmp_path):
    cfg_path = tmp_path / "trading.yaml"
    db_path = tmp_path / "exec.sqlite"
    cfg_path.write_text(
        """
pipeline:
  exchange_id: coinbase
symbols:
  - BTC/USD
execution:
  executor_mode: live
  db_path: __DB_PATH__
live:
  enabled: true
risk:
  max_daily_loss_quote: 0
""".replace("__DB_PATH__", str(db_path)),
        encoding="utf-8",
    )

    env_vars = {
        "CBP_MAX_TRADES_PER_DAY": "10",
        "CBP_MAX_DAILY_LOSS": "100",
        "CBP_MAX_DAILY_NOTIONAL": "1000",
        "CBP_MAX_ORDER_NOTIONAL": "100",
    }
    old_env = {name: os.environ.get(name) for name in env_vars}
    try:
        for name, value in env_vars.items():
            os.environ[name] = value
        out = pf.run_preflight(str(cfg_path))
    finally:
        for name, previous in old_env.items():
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous
    checks = {row["name"]: row for row in out.checks}

    assert out.ok is True
    assert checks["live_enabled"]["ok"] is True
