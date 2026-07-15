from __future__ import annotations

import importlib
import os


def test_resume_gate_blocks_when_not_safe(monkeypatch):
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(
        resume_gate,
        "ceremony_resume_provenance",
        lambda: {"ok": True, "reason": "ok"},
    )
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **kwargs: (False, "system_guard_halting", {"a": 1, "kwargs": kwargs}),
    )
    monkeypatch.setattr(resume_gate, "set_armed", lambda state, note="": {"armed": state, "note": note})

    out = resume_gate.resume_if_safe(note="test")
    assert out["ok"] is False
    assert out["resumed"] is False
    assert out["reason"] == "system_guard_halting"


def test_resume_gate_disarms_when_safe(monkeypatch):
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(
        resume_gate,
        "ceremony_resume_provenance",
        lambda: {"ok": True, "reason": "ok"},
    )
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **kwargs: (
            True,
            "ok",
            {
                "live_enabled": True,
                "system_guard": {"state": "HALTED"},
                "kwargs": kwargs,
            },
        ),
    )
    arm_calls: list[tuple[bool, str, str]] = []
    monkeypatch.setattr(
        resume_gate,
        "set_live_armed_state",
        lambda armed, *, writer, reason: arm_calls.append((bool(armed), writer, reason)) or {"armed": armed, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(resume_gate, "set_armed", lambda state, note="": {"armed": state, "note": note})
    monkeypatch.setattr(
        resume_gate,
        "set_system_guard_state",
        lambda state, *, writer, reason="": {"state": state, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(
        resume_gate,
        "record_live_resume_event",
        lambda **kwargs: {"ok": True, "event_id": "evt-resume", "path": "test://operator_events", "payload": kwargs},
    )

    out = resume_gate.resume_if_safe(note="safe")
    assert out["ok"] is True
    assert out["resumed"] is True
    assert out["armed_state"]["armed"] is True
    assert out["kill_switch"]["armed"] is False
    assert out["system_guard"]["state"] == "RUNNING"
    assert arm_calls == [(True, "resume_gate", "safe")]
    assert out["operator_event"]["ok"] is True
    assert out["details"]["kwargs"] == {
        "allow_kill_switch_armed": True,
        "allow_system_guard_halted": True,
    }


def test_resume_gate_rolls_back_when_operator_event_write_fails(monkeypatch):
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "YES")
    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(
        resume_gate,
        "ceremony_resume_provenance",
        lambda: {"ok": True, "reason": "ok"},
    )
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **kwargs: (True, "ok", {"live_enabled": True, "kwargs": kwargs}),
    )
    arm_calls: list[tuple[bool, str, str]] = []
    kill_calls: list[tuple[bool, str]] = []
    guard_calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        resume_gate,
        "set_live_armed_state",
        lambda armed, *, writer, reason: arm_calls.append((bool(armed), writer, reason)) or {"armed": armed, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(
        resume_gate,
        "set_armed",
        lambda state, note="": kill_calls.append((bool(state), str(note))) or {"armed": state, "note": note},
    )
    monkeypatch.setattr(
        resume_gate,
        "set_system_guard_state",
        lambda state, *, writer, reason="": guard_calls.append((state, writer, reason)) or {"state": state, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(
        resume_gate,
        "record_live_resume_event",
        lambda **_kwargs: {"ok": False, "reason": "operator_event_write_failed:PermissionError"},
    )

    out = resume_gate.resume_if_safe(note="safe")

    assert out["ok"] is False
    assert out["resumed"] is False
    assert out["reason"] == "operator_event_write_failed_live_resume_rolled_back"
    assert os.environ.get("CBP_EXECUTION_ARMED") is None
    assert out["operator_event"] == {"ok": False, "reason": "operator_event_write_failed:PermissionError"}
    assert arm_calls == [
        (True, "resume_gate", "safe"),
        (False, "resume_gate", "safe:rollback_operator_event_failed"),
    ]
    assert kill_calls == [
        (False, "safe"),
        (True, "safe:rollback_operator_event_failed"),
    ]
    assert guard_calls == [
        ("RUNNING", "resume_gate", "safe"),
        ("HALTED", "resume_gate", "safe:rollback_operator_event_failed"),
    ]


def test_resume_gate_rolls_back_kill_switch_when_system_guard_restore_fails(monkeypatch):
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
    cfg_state = {"execution": {"live_enabled": True}}
    calls: list[tuple[bool, str]] = []

    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: dict(cfg_state))
    monkeypatch.setattr(
        resume_gate,
        "ceremony_resume_provenance",
        lambda: {"ok": True, "reason": "ok"},
    )
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **kwargs: (True, "ok", {"live_enabled": True, "kwargs": kwargs}),
    )
    monkeypatch.setattr(
        resume_gate,
        "set_armed",
        lambda state, note="": calls.append((bool(state), str(note))) or {"armed": state, "note": note},
    )
    arm_calls: list[tuple[bool, str, str]] = []
    monkeypatch.setattr(
        resume_gate,
        "set_live_armed_state",
        lambda armed, *, writer, reason: arm_calls.append((bool(armed), writer, reason)) or {"armed": armed, "writer": writer, "reason": reason},
    )

    def _raise_guard(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(resume_gate, "set_system_guard_state", _raise_guard)

    out = resume_gate.resume_if_safe(note="safe")

    assert out["ok"] is False
    assert out["resumed"] is False
    assert out["reason"] == "system_guard_resume_failed:RuntimeError"
    assert out["armed_state"]["armed"] is False
    assert out["kill_switch"]["armed"] is True
    assert arm_calls == [
        (True, "resume_gate", "safe"),
        (False, "resume_gate", "safe:rollback_system_guard_failed"),
    ]
    assert calls == [
        (False, "safe"),
        (True, "safe:rollback_system_guard_failed"),
    ]
    assert "config_restore" not in out
    assert "save" not in out
    assert cfg_state["execution"]["live_enabled"] is True


def test_resume_gate_cold_state_refuses_without_config_write(monkeypatch):
    """
    Substrate backlog #17 proof: a cold/absent live config refuses before any
    provenance read, guard check, config write, arm, kill-switch, or
    system-guard mutation. The resume gate module no longer imports
    ``save_user_yaml`` at all, so it cannot re-enable live config.
    """
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)

    cfg_state = {"execution": {"live_enabled": False}}
    touched: list[str] = []

    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: dict(cfg_state))
    monkeypatch.setattr(
        resume_gate,
        "ceremony_resume_provenance",
        lambda: touched.append("provenance") or {"ok": True, "reason": "ok"},
    )
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **kwargs: touched.append("live_allowed") or (True, "ok", {}),
    )
    monkeypatch.setattr(
        resume_gate,
        "set_live_armed_state",
        lambda armed, *, writer, reason: touched.append("arm") or {"armed": armed},
    )
    monkeypatch.setattr(
        resume_gate,
        "set_armed",
        lambda state, note="": touched.append("kill_switch") or {"armed": state},
    )
    monkeypatch.setattr(
        resume_gate,
        "set_system_guard_state",
        lambda state, *, writer, reason="": touched.append("system_guard") or {"state": state},
    )

    out = resume_gate.resume_if_safe(note="cold")

    assert out["ok"] is False
    assert out["resumed"] is False
    assert out["reason"] == "live_not_enabled_ceremony_required"
    assert touched == []
    assert cfg_state["execution"]["live_enabled"] is False
    assert not hasattr(resume_gate, "save_user_yaml")
    assert "save" not in out
    assert "config_restore" not in out


def test_resume_gate_restores_persisted_arm_signal_visible_to_live_arming(monkeypatch, tmp_path):
    import services.admin.resume_gate as resume_gate
    from services.execution import live_arming

    importlib.reload(resume_gate)
    monkeypatch.setattr(resume_gate, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(
        resume_gate,
        "ceremony_resume_provenance",
        lambda: {"ok": True, "reason": "ok"},
    )
    monkeypatch.setattr(live_arming, "STATE_PATH", tmp_path / "live_arming.json")
    monkeypatch.setattr(live_arming, "load_user_yaml", lambda: {"execution": {"live_enabled": True}})
    monkeypatch.setattr(
        resume_gate,
        "live_allowed",
        lambda **_kwargs: (True, "ok", {"live_enabled": True, "system_guard": {"state": "HALTED"}}),
    )
    monkeypatch.setattr(resume_gate, "set_live_armed_state", live_arming.set_live_armed_state)
    monkeypatch.setattr(resume_gate, "set_armed", lambda state, note="": {"armed": state, "note": note})
    monkeypatch.setattr(
        resume_gate,
        "set_system_guard_state",
        lambda state, *, writer, reason="": {"state": state, "writer": writer, "reason": reason},
    )
    monkeypatch.setattr(
        resume_gate,
        "record_live_resume_event",
        lambda **kwargs: {"ok": True, "event_id": "evt-resume", "path": "test://operator_events", "payload": kwargs},
    )
    for name in ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED", "CBP_EXECUTION_LIVE_ENABLED", "ENABLE_LIVE_TRADING", "LIVE_TRADING", "CBP_LIVE_ARMED"):
        monkeypatch.delenv(name, raising=False)

    out = resume_gate.resume_if_safe(note="safe")
    armed, reason = live_arming.live_enabled_and_armed()

    assert out["ok"] is True
    assert armed is True
    assert reason == "env:CBP_EXECUTION_ARMED"


def test_startup_reconcile_runs_all(monkeypatch):
    import services.execution.startup_reconcile as startup_reconcile

    importlib.reload(startup_reconcile)
    monkeypatch.setattr(
        startup_reconcile,
        "reconcile_once",
        lambda venue, symbol: {"ok": symbol != "ETH/USD", "venue": venue, "symbol": symbol},
    )

    out = startup_reconcile.run_startup_reconciliation(venue="coinbase", symbols=["BTC/USD", "ETH/USD"])
    assert out["count"] == 2
    assert out["ok_count"] == 1
    assert out["fail_count"] == 1


def test_sizing_helpers():
    from services.execution import sizing

    qty = sizing.quote_to_base_qty(quote_notional=100.0, price=20.0, qty_step=0.1)
    assert qty == 5.0

    ok, reason, details = sizing.validate_order_size(qty=qty, price=20.0, min_notional=50.0)
    assert ok is True
    assert reason == "ok"
    assert details["notional"] == 100.0


def test_risk_gates_fail_closed_when_limits_missing(monkeypatch):
    import services.execution.risk_gates as risk_gates

    importlib.reload(risk_gates)
    monkeypatch.setattr(risk_gates.LiveRiskLimits, "from_trading_yaml", staticmethod(lambda: None))
    decision = risk_gates.evaluate_live_intent(intent={"qty": 1, "price": 100}, exec_db_path="/tmp/none.sqlite")
    assert decision.ok is False
    assert decision.reason == "limits_unconfigured"


def test_risk_ledger_store_roundtrip(tmp_path):
    from storage.risk_ledger_store_sqlite import RiskLedgerStoreSQLite

    db = RiskLedgerStoreSQLite(db_path=tmp_path / "risk_ledger.sqlite")
    db.upsert_daily_venue("2026-03-09", "coinbase", trades_count=3, notional_usd=120.0, realized_pnl_usd=4.5)
    row = db.get_daily_venue("2026-03-09", "coinbase")
    assert row["trades_count"] == 3
    assert row["notional_usd"] == 120.0

    db.upsert_daily("2026-03-09", "coinbase", "BTC/USD", trades_count=2, notional_usd=80.0, realized_pnl_usd=3.0)
    sym = db.get_daily("2026-03-09", "coinbase", "BTC/USD")
    assert sym["trades_count"] == 2
    assert sym["realized_pnl_usd"] == 3.0

    db.upsert_position(venue="coinbase", symbol="BTC/USD", qty=0.25, avg_cost=20000.0)
    pos = db.get_position(venue="coinbase", symbol="BTC/USD")
    assert pos is not None
    assert pos["qty"] == 0.25
