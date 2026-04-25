from __future__ import annotations

import importlib
import sys
import types


def _import_live_executor_with_guard_stub():
    sys.modules.pop("services.execution._executor_shared", None)
    original_guard = sys.modules.get("services.risk.market_quality_guard")
    mod = types.ModuleType("services.risk.market_quality_guard")
    mod.check = lambda *args, **kwargs: {"ok": True, "reason": "ok"}
    mod.check_market_quality = lambda *args, **kwargs: (True, "ok")
    sys.modules["services.risk.market_quality_guard"] = mod
    try:
        return importlib.import_module("services.execution._executor_shared")
    finally:
        if original_guard is None:
            sys.modules.pop("services.risk.market_quality_guard", None)
        else:
            sys.modules["services.risk.market_quality_guard"] = original_guard


def test_hard_off_guard_accepts_canonical_live_arm_signal(monkeypatch):
    le = _import_live_executor_with_guard_stub()
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.setattr(le, "live_armed_signal", lambda: (True, "env:CBP_EXECUTION_ARMED"))
    cfg = le.LiveCfg(enabled=True, observe_only=False, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD")

    ok, reason = le._hard_off_guard(cfg, operation="submit")

    assert ok is True
    assert reason == "ok"


def test_hard_off_guard_blocks_when_no_live_arm_signal(monkeypatch):
    le = _import_live_executor_with_guard_stub()
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    monkeypatch.setattr(le, "live_armed_signal", lambda: (False, "live_not_armed"))
    cfg = le.LiveCfg(enabled=True, observe_only=False, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD")

    ok, reason = le._hard_off_guard(cfg, operation="submit")

    assert ok is False
    assert reason == "live_not_armed"
