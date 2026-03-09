from __future__ import annotations

import asyncio

import pytest

from services.live_trader_fleet import main as fleet_main
from services.live_trader_multi import main as multi_main


class _StopLoop(RuntimeError):
    pass


class _GuardStore:
    def __init__(self) -> None:
        self.orders: list[tuple[str, str, str, float, float]] = []

    async def record_order(self, venue: str, symbol: str, side: str, qty: float, price: float) -> None:
        self.orders.append((venue, symbol, side, qty, price))


class _PnLStore:
    def __init__(self) -> None:
        self.fills: list[tuple[str, str, str, float, float]] = []

    async def record_fill(self, venue: str, symbol: str, side: str, qty: float, price: float, fee: float = 0.0, fee_ccy: str | None = None) -> None:
        self.fills.append((venue, symbol, side, qty, price))


@pytest.mark.parametrize(
    ("module", "runner_name"),
    [
        (multi_main, "live_trader_multi"),
        (fleet_main, "live_trader_fleet"),
    ],
)
def test_live_runner_records_guard_order_after_fill(monkeypatch, module, runner_name):
    guard = _GuardStore()
    pnl = _PnLStore()

    async def _sleep(_seconds: float) -> None:
        raise _StopLoop(runner_name)

    monkeypatch.setenv("CBP_RUN_MODE", "live")
    monkeypatch.setenv("CBP_VENUE", "coinbase")
    monkeypatch.setattr(module, "ExecutionGuardStoreSQLite", lambda: guard)
    monkeypatch.setattr(module, "PnLStoreSQLite", lambda: pnl)
    monkeypatch.setattr(module, "load_gates", lambda: object())
    monkeypatch.setattr(module, "live_allowed", lambda: (True, "ok", {}))
    monkeypatch.setattr(module, "should_allow_order", lambda *args, **kwargs: (True, "ok"))
    monkeypatch.setattr(module, "env_symbol", lambda *, venue=None, out="dash": "BTC-USD")
    monkeypatch.setattr(module, "set_health", lambda *args, **kwargs: None)
    monkeypatch.setattr(module.asyncio, "sleep", _sleep)

    with pytest.raises(_StopLoop, match=runner_name):
        asyncio.run(module.main())

    assert pnl.fills == [("simulated", "BTC-USD", "buy", 0.001, 60000.0)]
    assert guard.orders == [("simulated", "BTC-USD", "buy", 0.001, 60000.0)]
