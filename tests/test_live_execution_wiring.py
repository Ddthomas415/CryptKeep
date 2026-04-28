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
        lambda venue, creds, enable_rate_limit=True, sandbox=False, require_sandbox=False: dummy_exchange,
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


def test_live_exchange_adapter_passes_sandbox_to_exchange_factory(monkeypatch):
    seen: dict = {}

    monkeypatch.setattr(
        live_exchange_adapter,
        "load_exchange_credentials",
        lambda venue: {"apiKey": "k", "secret": "s", "password": None, "venue": venue},
    )

    def _fake_make_exchange(venue, creds, enable_rate_limit=True, sandbox=False, require_sandbox=False):
        seen["venue"] = venue
        seen["sandbox"] = sandbox
        seen["require_sandbox"] = require_sandbox
        return object()

    monkeypatch.setattr(live_exchange_adapter, "make_exchange", _fake_make_exchange)

    ad = live_exchange_adapter.LiveExchangeAdapter("coinbase", sandbox=True)

    assert ad.creds_meta()["sandbox"] is True
    assert seen == {"venue": "coinbase", "sandbox": True, "require_sandbox": True}


def test_live_consumers_call_adapter_submit_order():
    root = Path(__file__).resolve().parents[1]
    targets = (
        "services/execution/intent_consumer.py",
        "services/execution/live_intent_consumer.py",
        "services/execution/live_reconciler.py",
    )
    for rel in targets:
        txt = (root / rel).read_text(encoding="utf-8", errors="replace")
        assert "LiveExchangeAdapter(venue, sandbox=" in txt
        if "consumer.py" in rel:
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
    attr_name = "create_" + "order"
    out = getattr(ad, attr_name)(
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

def test_live_intent_consumer_recovers_existing_remote_order_before_submit(monkeypatch, tmp_path):
    import importlib

    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")
    monkeypatch.setenv("CBP_LIVE_ENABLED", "1")

    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod
    import storage.live_trading_sqlite as trading_mod
    import services.execution.live_intent_consumer as consumer

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    importlib.reload(trading_mod)
    importlib.reload(consumer)

    qdb = queue_mod.LiveIntentQueueSQLite()
    qdb.upsert_intent({
        "intent_id": "recover-before-submit",
        "created_ts": "2026-04-02T12:00:00Z",
        "ts": "2026-04-02T12:00:00Z",
        "source": "strategy",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 0.5,
        "limit_price": 100.0,
        "status": "queued",
        "last_error": None,
        "client_order_id": "cid-recover-before-submit",
        "exchange_order_id": None,
    })

    monkeypatch.setattr(consumer, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(consumer, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(consumer, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(consumer, "mq_check", lambda venue, symbol: {"ok": True, "last": 100.0})
    monkeypatch.setattr(consumer, "_risk_check_and_claim", lambda db, notional_est: (True, None))

    class Decision:
        allowed = True
        side = "buy"
        order_type = "limit"
        qty = 0.5
        limit_price = 100.0
        reason = "ok"

    async def fake_decide_order(**kwargs):
        return Decision()

    monkeypatch.setattr(consumer, "decide_order", fake_decide_order)

    submit_called = {"value": False}

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            assert client_order_id == "cid-recover-before-submit"
            return {"id": "ex-recovered-1", "clientOrderId": client_order_id}

        def submit_order(self, **kwargs):
            submit_called["value"] = True
            raise AssertionError("submit_order must not be called when recovery succeeds")

        def close(self):
            pass

    monkeypatch.setattr(consumer, "LiveExchangeAdapter", FakeAdapter)

    loops = {"count": 0}

    def fake_sleep(_seconds):
        loops["count"] += 1
        if loops["count"] >= 1:
            consumer.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            consumer.STOP_FILE.write_text("stop\n")

    monkeypatch.setattr(consumer.time, "sleep", fake_sleep)

    consumer.run_forever()

    row = qdb.list_intents(limit=10)[0]
    assert row["status"] == "submitted"
    assert row["client_order_id"] == "cid-recover-before-submit"
    assert row["exchange_order_id"] == "ex-recovered-1"
    assert submit_called["value"] is False

    orders = trading_mod.LiveTradingSQLite().list_orders(limit=10)
    assert orders[0]["status"] == "submitted"
    assert orders[0]["exchange_order_id"] == "ex-recovered-1"


def test_live_intent_consumer_missing_submit_exchange_id_becomes_submit_unknown(monkeypatch, tmp_path):
    import importlib

    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "1")
    monkeypatch.setenv("CBP_LIVE_ENABLED", "1")

    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod
    import storage.live_trading_sqlite as trading_mod
    import services.execution.live_intent_consumer as consumer

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    importlib.reload(trading_mod)
    importlib.reload(consumer)

    qdb = queue_mod.LiveIntentQueueSQLite()
    qdb.upsert_intent({
        "intent_id": "missing-submit-exchange-id",
        "created_ts": "2026-04-02T12:00:00Z",
        "ts": "2026-04-02T12:00:00Z",
        "source": "strategy",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 0.5,
        "limit_price": 100.0,
        "status": "queued",
        "last_error": None,
        "client_order_id": "cid-missing-submit-exchange-id",
        "exchange_order_id": None,
    })

    monkeypatch.setattr(consumer, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(consumer, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(consumer, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(consumer, "mq_check", lambda venue, symbol: {"ok": True, "last": 100.0})
    monkeypatch.setattr(consumer, "_risk_check_and_claim", lambda db, notional_est: (True, None))

    class Decision:
        allowed = True
        side = "buy"
        order_type = "limit"
        qty = 0.5
        limit_price = 100.0
        reason = "ok"

    async def fake_decide_order(**kwargs):
        return Decision()

    monkeypatch.setattr(consumer, "decide_order", fake_decide_order)

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def find_order_by_client_oid(self, symbol, client_order_id):
            return None

        def submit_order(self, **kwargs):
            return {}

        def close(self):
            pass

    monkeypatch.setattr(consumer, "LiveExchangeAdapter", FakeAdapter)

    loops = {"count": 0}

    def fake_sleep(_seconds):
        loops["count"] += 1
        if loops["count"] >= 1:
            consumer.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            consumer.STOP_FILE.write_text("stop\n")

    monkeypatch.setattr(consumer.time, "sleep", fake_sleep)

    consumer.run_forever()

    row = qdb.list_intents(limit=10)[0]
    assert row["status"] == "submit_unknown"
    assert row["client_order_id"] == "cid-missing-submit-exchange-id"
    assert row["exchange_order_id"] is None
    assert row["last_error"] == "submit_response_missing_exchange_order_id"

    orders = trading_mod.LiveTradingSQLite().list_orders(limit=10)
    assert orders[0]["status"] == "submit_unknown"
    assert orders[0]["exchange_order_id"] is None
    assert orders[0]["last_error"] == "submit_response_missing_exchange_order_id"
