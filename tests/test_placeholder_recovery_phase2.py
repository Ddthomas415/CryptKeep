from __future__ import annotations

import importlib


def test_resume_gate_blocks_when_not_safe(monkeypatch):
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
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
    monkeypatch.setattr(resume_gate, "set_armed", lambda state, note="": {"armed": state, "note": note})
    monkeypatch.setattr(
        resume_gate,
        "set_system_guard_state",
        lambda state, *, writer, reason="": {"state": state, "writer": writer, "reason": reason},
    )

    out = resume_gate.resume_if_safe(note="safe")
    assert out["ok"] is True
    assert out["resumed"] is True
    assert out["kill_switch"]["armed"] is False
    assert out["system_guard"]["state"] == "RUNNING"
    assert out["details"]["kwargs"] == {
        "allow_kill_switch_armed": True,
        "allow_system_guard_halted": True,
    }


def test_resume_gate_rolls_back_kill_switch_when_system_guard_restore_fails(monkeypatch):
    import services.admin.resume_gate as resume_gate

    importlib.reload(resume_gate)
    calls: list[tuple[bool, str]] = []
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

    def _raise_guard(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(resume_gate, "set_system_guard_state", _raise_guard)

    out = resume_gate.resume_if_safe(note="safe")

    assert out["ok"] is False
    assert out["resumed"] is False
    assert out["reason"] == "system_guard_resume_failed:RuntimeError"
    assert out["kill_switch"]["armed"] is True
    assert calls == [
        (False, "safe"),
        (True, "safe:rollback_system_guard_failed"),
    ]


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


def test_risk_gates_returns_unconfigured_when_limits_missing(monkeypatch):
    import services.execution.risk_gates as risk_gates

    importlib.reload(risk_gates)
    monkeypatch.setattr(risk_gates.LiveRiskLimits, "from_trading_yaml", staticmethod(lambda: None))
    decision = risk_gates.evaluate_live_intent(intent={"qty": 1, "price": 100}, exec_db_path="/tmp/none.sqlite")
    assert decision.ok is True
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
