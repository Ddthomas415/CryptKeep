from __future__ import annotations

import importlib
import sys
import types


def _import_live_executor_with_guard_stub():
    sys.modules.pop("services.execution.live_executor", None)
    mod = types.ModuleType("services.risk.market_quality_guard")
    mod.check_market_quality = lambda *args, **kwargs: {"ok": True}
    sys.modules["services.risk.market_quality_guard"] = mod
    return importlib.import_module("services.execution.live_executor")


def test_hard_off_guard_accepts_persisted_live_arm_signal(monkeypatch):
    le = _import_live_executor_with_guard_stub()
    monkeypatch.delenv("LIVE_TRADING", raising=False)
    monkeypatch.setattr(le, "live_armed_signal", lambda: (True, "state:live_armed"))
    cfg = le.LiveCfg(enabled=True, observe_only=False, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD")

    ok, reason = le._hard_off_guard(cfg, operation="submit")

    assert ok is True
    assert reason == "ok"


def test_hard_off_guard_blocks_when_no_live_arm_signal(monkeypatch):
    le = _import_live_executor_with_guard_stub()
    monkeypatch.delenv("LIVE_TRADING", raising=False)
    monkeypatch.setattr(le, "live_armed_signal", lambda: (False, "live_not_armed"))
    cfg = le.LiveCfg(enabled=True, observe_only=False, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD")

    ok, reason = le._hard_off_guard(cfg, operation="submit")

    assert ok is False
    assert reason == "live_not_armed"
