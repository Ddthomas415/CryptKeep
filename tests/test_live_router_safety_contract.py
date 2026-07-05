from __future__ import annotations

import asyncio

from services.execution.safety import SafetyGates
from services.live_router.router import decide_order


class _Store:
    def get_today_metrics(self):
        return {"trades": 0, "approx_realized_pnl": 0.0}



def test_live_router_uses_explicit_reference_price_for_safety_gate(monkeypatch):
    monkeypatch.setattr("services.live_router.router.is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr("services.live_router.router.load_user_config", lambda: {})
    monkeypatch.setattr("services.live_router.router.load_gates", lambda: SafetyGates(min_order_notional=100.0))
    monkeypatch.setattr("services.live_router.router.ExecutionGuardStoreSQLite", lambda: _Store())

    decision = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=1.0,
            overrides={"reference_price": 60000.0},
        )
    )

    assert decision.allowed is True
    assert decision.reason == "ok"
    assert decision.limit_price == 60000.0
    assert decision.meta["reference_price"] == 60000.0
    assert decision.meta["safety_ok"] is True


def test_live_router_blocks_without_reference_price(monkeypatch):
    monkeypatch.setattr("services.live_router.router.is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr("services.live_router.router.load_user_config", lambda: {})
    monkeypatch.setattr(
        "services.live_router.router.should_allow_order",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("safety should not run without reference price")
        ),
    )

    decision = asyncio.run(decide_order(venue="coinbase", symbol_norm="BTC/USD", delta_qty=1.0))

    assert decision.allowed is False
    assert decision.reason == "no_reference_price"
    assert decision.limit_price is None
    assert decision.meta["reference_price"] is None
    assert decision.meta["reference_price_reason"] == "missing_or_invalid"


def test_live_router_blocks_invalid_reference_price(monkeypatch):
    monkeypatch.setattr("services.live_router.router.is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr("services.live_router.router.load_user_config", lambda: {})

    decision = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=1.0,
            overrides={"reference_price": 0.0},
        )
    )

    assert decision.allowed is False
    assert decision.reason == "no_reference_price"


def test_live_router_safety_gate_error_fails_closed(monkeypatch):
    monkeypatch.setattr("services.live_router.router.is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr("services.live_router.router.load_user_config", lambda: {})
    monkeypatch.setattr(
        "services.live_router.router.load_gates",
        lambda: (_ for _ in ()).throw(RuntimeError("gate_config_failed")),
    )

    decision = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=1.0,
            overrides={"reference_price": 60000.0},
        )
    )

    assert decision.allowed is False
    assert decision.reason == "safety:safety_check_error_fail_closed:RuntimeError"
    assert decision.meta["safety_ok"] is False



def test_live_router_blocks_zero_delta_without_running_gates(monkeypatch):
    monkeypatch.setattr("services.live_router.router.is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(
        "services.live_router.router.should_allow_order",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("safety should not run for zero delta")),
    )

    decision = asyncio.run(decide_order(venue="coinbase", symbol_norm="BTC/USD", delta_qty=0.0))

    assert decision.allowed is False
    assert decision.reason == "zero_delta"
    assert decision.order_type == "none"
    assert decision.limit_price is None



def test_live_router_still_blocks_when_notional_really_below_minimum(monkeypatch):
    monkeypatch.setattr("services.live_router.router.is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr("services.live_router.router.load_user_config", lambda: {})
    monkeypatch.setattr("services.live_router.router.load_gates", lambda: SafetyGates(min_order_notional=100.0))
    monkeypatch.setattr("services.live_router.router.ExecutionGuardStoreSQLite", lambda: _Store())

    decision = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=0.001,
            overrides={"reference_price": 50.0},
        )
    )

    assert decision.allowed is False
    assert decision.reason == "safety:min_order_notional"
