from __future__ import annotations

from pathlib import Path

import services.execution.live_exchange_adapter as live_exchange_adapter
from services.execution.execution_context import ExecutionContext


def _patch_adapter_deps(monkeypatch):
    monkeypatch.setattr(
        live_exchange_adapter,
        "load_exchange_credentials",
        lambda venue: {"apiKey": "k", "secret": "s", "password": None, "venue": venue},
    )
    dummy_exchange = object()
    monkeypatch.setattr(
        live_exchange_adapter,
        "make_exchange",
        lambda venue, creds, enable_rate_limit=True: dummy_exchange,
    )
    monkeypatch.setattr(live_exchange_adapter, "map_symbol", lambda venue, symbol: "BTC/USD")
    return dummy_exchange


def test_live_exchange_adapter_submit_order_routes_through_place_order(monkeypatch):
    dummy_exchange = _patch_adapter_deps(monkeypatch)
    seen: dict = {}

    def _fake_place_order(ex, *args, **kwargs):
        seen["ex"] = ex
        seen["args"] = args
        seen["kwargs"] = kwargs
        return {"id": "ex-order-1"}

    monkeypatch.setattr(live_exchange_adapter, "place_order", _fake_place_order)
    ad = live_exchange_adapter.LiveExchangeAdapter("coinbase")
    out = ad.submit_order(
        canonical_symbol="BTC/USD",
        side="BUY",
        order_type="LIMIT",
        qty=0.25,
        limit_price=101.5,
        client_order_id="cid-1",
    )
    assert out["id"] == "ex-order-1"
    assert seen["ex"] is dummy_exchange
    assert seen["args"] == ("BTC/USD", "limit", "buy", 0.25, 101.5, {"clientOrderId": "cid-1"})
    assert seen["kwargs"] == {}


def test_live_exchange_adapter_market_order_omits_price(monkeypatch):
    _patch_adapter_deps(monkeypatch)
    seen: dict = {}

    def _fake_place_order(ex, *args, **kwargs):
        seen["args"] = args
        return {"id": "ex-order-2"}

    monkeypatch.setattr(live_exchange_adapter, "place_order", _fake_place_order)
    ad = live_exchange_adapter.LiveExchangeAdapter("coinbase")
    ad.submit_order(
        canonical_symbol="BTC/USD",
        side="sell",
        order_type="market",
        qty=1.0,
        limit_price=999.0,
        client_order_id="cid-2",
    )
    assert seen["args"][4] is None


def test_live_exchange_adapter_passes_context_only_when_provided(monkeypatch):
    _patch_adapter_deps(monkeypatch)
    seen: dict = {}

    def _fake_place_order(ex, *args, **kwargs):
        seen["kwargs"] = kwargs
        return {"id": "ex-order-ctx"}

    monkeypatch.setattr(live_exchange_adapter, "place_order", _fake_place_order)
    ad = live_exchange_adapter.LiveExchangeAdapter("coinbase")
    ctx = ExecutionContext(
        mode="live",
        authority="LIVE_SUBMIT_OWNER",
        origin="test_live_execution_wiring",
    )
    out = ad.submit_order(
        canonical_symbol="BTC/USD",
        side="buy",
        order_type="limit",
        qty=0.1,
        limit_price=100.0,
        client_order_id="cid-ctx",
        context=ctx,
    )

    assert out["id"] == "ex-order-ctx"
    assert seen["kwargs"] == {"context": ctx}


def test_live_consumers_call_adapter_submit_order():
    root = Path(__file__).resolve().parents[1]
    targets = (
        "services/execution/intent_consumer.py",
        "services/execution/live_intent_consumer.py",
    )
    for rel in targets:
        txt = (root / rel).read_text(encoding="utf-8", errors="replace")
        assert "ad.submit_order(" in txt
        assert "resp = place_order(" not in txt


def test_live_exchange_adapter_compat_alias_available(monkeypatch):
    _patch_adapter_deps(monkeypatch)
    seen: dict = {}

    def _fake_place_order(ex, *args, **kwargs):
        seen["args"] = args
        return {"id": "ex-order-compat"}

    monkeypatch.setattr(live_exchange_adapter, "place_order", _fake_place_order)
    ad = live_exchange_adapter.LiveExchangeAdapter("coinbase")
    out = getattr(ad, "create_order")(
        canonical_symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=0.1,
        limit_price=None,
        client_order_id="cid-compat",
    )
    assert out["id"] == "ex-order-compat"
    assert seen["args"][0] == "BTC/USD"


def test_live_exchange_adapter_cancel_order_routes_through_lifecycle_boundary(monkeypatch):
    dummy_exchange = _patch_adapter_deps(monkeypatch)
    seen: dict = {}

    def _fake_cancel(ex, *, venue: str, symbol: str, order_id: str, source: str):
        seen["ex"] = ex
        seen["venue"] = venue
        seen["symbol"] = symbol
        seen["order_id"] = order_id
        seen["source"] = source
        return {"status": "canceled"}

    monkeypatch.setattr(live_exchange_adapter, "cancel_order_via_boundary", _fake_cancel)
    ad = live_exchange_adapter.LiveExchangeAdapter("coinbase")
    out = ad.cancel_order("BTC/USD", "oid-1")
    assert out["status"] == "canceled"
    assert seen == {
        "ex": dummy_exchange,
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "order_id": "oid-1",
        "source": "live_exchange_adapter.cancel_order",
    }


def test_live_exchange_adapter_fetch_order_routes_through_lifecycle_boundary(monkeypatch):
    dummy_exchange = _patch_adapter_deps(monkeypatch)
    seen: dict = {}

    def _fake_fetch(ex, *, venue: str, symbol: str, order_id: str, source: str):
        seen["ex"] = ex
        seen["venue"] = venue
        seen["symbol"] = symbol
        seen["order_id"] = order_id
        seen["source"] = source
        return {"id": "oid-2", "status": "open"}

    monkeypatch.setattr(live_exchange_adapter, "fetch_order_via_boundary", _fake_fetch)
    ad = live_exchange_adapter.LiveExchangeAdapter("coinbase")
    out = ad.fetch_order("BTC/USD", "oid-2")
    assert out["id"] == "oid-2"
    assert seen == {
        "ex": dummy_exchange,
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "order_id": "oid-2",
        "source": "live_exchange_adapter.fetch_order",
    }


def test_live_exchange_adapter_fetch_my_trades_routes_through_lifecycle_boundary(monkeypatch):
    dummy_exchange = _patch_adapter_deps(monkeypatch)
    seen: dict = {}

    def _fake_fetch_trades(ex, *, venue: str, symbol: str, since_ms: int | None = None, limit: int | None = 200, source: str):
        seen["ex"] = ex
        seen["venue"] = venue
        seen["symbol"] = symbol
        seen["since_ms"] = since_ms
        seen["limit"] = limit
        seen["source"] = source
        return [{"id": "trade-1"}]

    monkeypatch.setattr(live_exchange_adapter, "fetch_my_trades_via_boundary", _fake_fetch_trades)
    ad = live_exchange_adapter.LiveExchangeAdapter("coinbase")
    out = ad.fetch_my_trades("BTC/USD", since_ms=123, limit=10)
    assert out == [{"id": "trade-1"}]
    assert seen == {
        "ex": dummy_exchange,
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "since_ms": 123,
        "limit": 10,
        "source": "live_exchange_adapter.fetch_my_trades",
    }


def test_live_exchange_adapter_submit_order_binance_params(monkeypatch):
    _patch_adapter_deps(monkeypatch)
    seen: dict = {}

    def _fake_place_order(ex, *args, **kwargs):
        seen["args"] = args
        return {"id": "ex-order-binance"}

    monkeypatch.setattr(live_exchange_adapter, "place_order", _fake_place_order)
    ad = live_exchange_adapter.LiveExchangeAdapter("binanceus")
    out = ad.submit_order(
        canonical_symbol="BTC/USD",
        side="buy",
        order_type="limit",
        qty=0.3,
        limit_price=100.0,
        client_order_id="cid-b-1",
        params={"timeInForce": "gtc", "foo": "drop-me"},
    )
    assert out["id"] == "ex-order-binance"
    params = seen["args"][5]
    assert params["newClientOrderId"] == "cid-b-1"
    assert params["timeInForce"] == "GTC"
    assert "foo" not in params
