import asyncio
from unittest.mock import patch

from services.execution.order_manager import OrderManager


class DummyExchange:
    def __init__(self) -> None:
        self.cancel_called = []
        self.create_called = []

    async def cancel_order(self, order_id: str, symbol: str) -> dict:
        self.cancel_called.append((order_id, symbol))
        return {"status": "canceled"}

    async def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float, params: dict) -> dict:
        self.create_called.append(
            {
                "symbol": symbol,
                "order_type": order_type,
                "side": side,
                "amount": amount,
                "price": price,
                "params": params,
            }
        )
        return {"id": "new-order", "status": "open"}


def test_cancel_and_replace_runs(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_MAX_TRADES_PER_DAY", "10")
    monkeypatch.setenv("CBP_MAX_DAILY_LOSS", "1000")
    monkeypatch.setenv("CBP_MAX_DAILY_NOTIONAL", "100000")
    monkeypatch.setenv("CBP_MAX_ORDER_NOTIONAL", "100000")
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")
    # Patch enforce to avoid messing with risk_daily
    dummy_db = tmp_path / "dummy.db"
    with patch("services.execution.place_order._enforce_fail_closed", return_value=(str(dummy_db), 0.0)):
        async def run():
            mgr = OrderManager()
            exchange = DummyExchange()
            res = await mgr.cancel_and_replace(
                exchange,
                venue="coinbase",
                symbol="BTC/USD",
                side="buy",
                order_id="old-oid",
                new_qty=0.5,
                new_price=21000.0,
                params={"test": True},
                cancel_reason="strategy R/R",
            )
            return res, exchange

        result, exchange = asyncio.run(run())
    assert exchange.cancel_called == [("old-oid", "BTC/USD")]
    assert exchange.create_called[0]["order_type"] == "limit"
    assert result.get("id") == "new-order"


def test_cancel_and_replace_routes_cancel_through_lifecycle_boundary(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_MAX_TRADES_PER_DAY", "10")
    monkeypatch.setenv("CBP_MAX_DAILY_LOSS", "1000")
    monkeypatch.setenv("CBP_MAX_DAILY_NOTIONAL", "100000")
    monkeypatch.setenv("CBP_MAX_ORDER_NOTIONAL", "100000")
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")
    dummy_db = tmp_path / "dummy.db"
    seen: dict = {}

    async def _fake_cancel(ex, *, venue: str, symbol: str, order_id: str, reason: str | None = None, source: str):
        seen["ex"] = ex
        seen["venue"] = venue
        seen["symbol"] = symbol
        seen["order_id"] = order_id
        seen["reason"] = reason
        seen["source"] = source
        return {"status": "canceled"}

    with patch("services.execution.place_order._enforce_fail_closed", return_value=(str(dummy_db), 0.0)):
        with patch("services.execution.order_manager.cancel_order_async_via_boundary", _fake_cancel):
            async def run():
                mgr = OrderManager()
                exchange = DummyExchange()
                res = await mgr.cancel_and_replace(
                    exchange,
                    venue="coinbase",
                    symbol="BTC/USD",
                    side="buy",
                    order_id="old-oid",
                    new_qty=0.5,
                    new_price=21000.0,
                    params={"test": True},
                    cancel_reason="strategy R/R",
                )
                return res, exchange

            result, exchange = asyncio.run(run())

    assert seen == {
        "ex": exchange,
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "order_id": "old-oid",
        "reason": "strategy R/R",
        "source": "order_manager.cancel_and_replace",
    }
    assert result.get("id") == "new-order"
