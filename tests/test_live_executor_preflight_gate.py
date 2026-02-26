from __future__ import annotations

from types import SimpleNamespace

from services.execution import live_executor as le


def test_preflight_gate_circuit_breaker_trip_and_pause(monkeypatch):
    monkeypatch.setenv("CBP_LIVE_PREFLIGHT_ENFORCE", "1")
    monkeypatch.setenv("CBP_LIVE_PREFLIGHT_FAIL_THRESHOLD", "2")
    monkeypatch.setenv("CBP_LIVE_PREFLIGHT_PAUSE_SECONDS", "60")

    def _always_fail(*, cfg_path: str = "config/trading.yaml"):
        return SimpleNamespace(
            ok=False,
            checks=[{"name": "db_writable", "ok": False, "severity": "ERROR", "detail": "db down"}],
        )

    monkeypatch.setattr(le, "run_preflight", _always_fail)

    state = le._PreflightCircuitState()
    cfg = le.LiveCfg(enabled=True)

    ok1, reason1, meta1 = le._check_preflight_gate(cfg, state=state, now_ts=100.0)
    assert ok1 is False
    assert reason1 == "PREFLIGHT_FAILED"
    assert meta1.get("consecutive_failures") == 1

    ok2, reason2, meta2 = le._check_preflight_gate(cfg, state=state, now_ts=101.0)
    assert ok2 is False
    assert reason2 == "CIRCUIT_BREAKER_TRIPPED"
    assert float(meta2.get("pause_until_ts") or 0.0) > 101.0

    ok3, reason3, meta3 = le._check_preflight_gate(cfg, state=state, now_ts=102.0)
    assert ok3 is False
    assert reason3 == "CIRCUIT_BREAKER_PAUSED"
    assert float(meta3.get("pause_remaining_s") or 0.0) > 0.0


def test_preflight_gate_success_resets_failure_counter(monkeypatch):
    monkeypatch.setenv("CBP_LIVE_PREFLIGHT_ENFORCE", "1")
    monkeypatch.setenv("CBP_LIVE_PREFLIGHT_FAIL_THRESHOLD", "3")
    monkeypatch.setenv("CBP_LIVE_PREFLIGHT_PAUSE_SECONDS", "30")

    calls = {"n": 0}

    def _flip(*, cfg_path: str = "config/trading.yaml"):
        calls["n"] += 1
        if calls["n"] == 1:
            return SimpleNamespace(
                ok=False,
                checks=[{"name": "symbols_configured", "ok": False, "severity": "ERROR", "detail": "symbols missing"}],
            )
        return SimpleNamespace(ok=True, checks=[{"name": "all_good", "ok": True, "severity": "INFO", "detail": "ok"}])

    monkeypatch.setattr(le, "run_preflight", _flip)

    state = le._PreflightCircuitState()
    cfg = le.LiveCfg(enabled=True)

    ok1, reason1, _ = le._check_preflight_gate(cfg, state=state, now_ts=100.0)
    assert ok1 is False
    assert reason1 == "PREFLIGHT_FAILED"
    assert state.consecutive_failures == 1

    ok2, reason2, meta2 = le._check_preflight_gate(cfg, state=state, now_ts=101.0)
    assert ok2 is True
    assert reason2 == "OK"
    assert isinstance(meta2.get("checks"), list)
    assert state.consecutive_failures == 0


def test_preflight_gate_can_be_disabled(monkeypatch):
    monkeypatch.setenv("CBP_LIVE_PREFLIGHT_ENFORCE", "0")
    state = le._PreflightCircuitState()
    cfg = le.LiveCfg(enabled=True)

    ok, reason, meta = le._check_preflight_gate(cfg, state=state, now_ts=100.0)
    assert ok is True
    assert reason == "PREFLIGHT_GATE_DISABLED"
    assert meta.get("enforced") is False
