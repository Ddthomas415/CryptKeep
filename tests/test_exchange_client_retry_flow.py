import pytest
import socket

from services.execution.client_order_id import make_client_order_id as canonical_make_client_order_id
from services.execution.execution_context import ExecutionContext
from services.execution.order_reconciliation import SafeToRetryAfterReconciliation
from storage.order_dedupe_store_sqlite import OrderDedupeStore as ExecutionOrderDedupeStore


@pytest.fixture(autouse=True)
def offline_client_boundaries(monkeypatch):
    from services.execution import exchange_client as subject
    def refuse(*args, **kwargs):
        raise AssertionError("private/network call forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(subject, "ensure_dirs", lambda: None)
    monkeypatch.setattr(subject, "load_exchange_credentials", refuse)


class DummyStore:
    def __init__(self):
        self.claimed = []
        self.unknown = []
        self.submitted = []
        self.errors = []

    def claim(self, **kwargs):
        self.claimed.append(kwargs)
        return {"status": "created", "_inserted": True, "_submit_claimed": True,
                **{key: kwargs[key] for key in ("exchange_id", "intent_id", "symbol", "client_order_id")}}

    def get(self, **kwargs):
        return None

    def mark_submitted(self, **kwargs):
        self.submitted.append(kwargs)

    def mark_unknown(self, **kwargs):
        self.unknown.append(kwargs)

    def mark_error(self, **kwargs):
        self.errors.append(kwargs)


class DummyExchange:
    def __init__(self, exc):
        self.exc = exc

    def create_order(self, *args, **kwargs):
        raise self.exc

    def close(self):
        pass


class DummySuccessExchange:
    def close(self):
        pass


def test_ambiguous_submit_requires_reconciliation_before_retry(monkeypatch, tmp_path):
    from services.execution.exchange_client import ExchangeClient

    store = DummyStore()

    monkeypatch.setattr("services.execution.exchange_client.OrderDedupeStore", lambda *a, **k: store)
    monkeypatch.setattr("services.execution.exchange_client.load_exchange_credentials", lambda exchange_id: {"apiKey": "x"})
    monkeypatch.setattr(ExchangeClient, "build", lambda self: DummyExchange(TimeoutError("invented timeout")))
    monkeypatch.setattr("services.execution.exchange_client.ensure_dirs", lambda: None)
    monkeypatch.setattr("services.execution.exchange_client.place_order", lambda ex, *a, **k: ex.create_order())
    monkeypatch.setattr("services.execution.exchange_client.client_id_param", lambda exchange_id, client_id: {"clientOrderId": client_id})
    monkeypatch.setattr(
        "services.execution.exchange_client.reconcile_ambiguous_submission",
        lambda **kwargs: type("R", (), {"outcome": "inconclusive"})(),
    )

    client = ExchangeClient("binance")

    with pytest.raises(RuntimeError, match="ambiguous_submit_blocked:inconclusive"):
        client.submit_order(
            intent_id="i1",
            client_id="cid-1",
            symbol="BTC/USDT",
            side="buy",
            amount=1.0,
            price=None,
            order_type="market",
            exec_db=str(tmp_path / "fixture.sqlite"),
        )

    assert len(store.unknown) == 1


def test_ambiguous_submit_allows_retry_only_when_confirmed_not_placed(monkeypatch, tmp_path):
    from services.execution.exchange_client import ExchangeClient

    store = DummyStore()

    monkeypatch.setattr("services.execution.exchange_client.OrderDedupeStore", lambda *a, **k: store)
    monkeypatch.setattr("services.execution.exchange_client.load_exchange_credentials", lambda exchange_id: {"apiKey": "x"})
    monkeypatch.setattr(ExchangeClient, "build", lambda self: DummyExchange(TimeoutError("invented timeout")))
    monkeypatch.setattr("services.execution.exchange_client.ensure_dirs", lambda: None)
    monkeypatch.setattr("services.execution.exchange_client.place_order", lambda ex, *a, **k: ex.create_order())
    monkeypatch.setattr("services.execution.exchange_client.client_id_param", lambda exchange_id, client_id: {"clientOrderId": client_id})
    monkeypatch.setattr(
        "services.execution.exchange_client.reconcile_ambiguous_submission",
        lambda **kwargs: type("R", (), {"outcome": "confirmed_not_placed"})(),
    )

    client = ExchangeClient("binance")

    with pytest.raises(SafeToRetryAfterReconciliation):
        client.submit_order(
            intent_id="i1",
            client_id="cid-1",
            symbol="BTC/USDT",
            side="buy",
            amount=1.0,
            price=None,
            order_type="market",
            exec_db=str(tmp_path / "fixture.sqlite"),
        )

    assert len(store.unknown) == 1


def test_submit_order_uses_execution_dedupe_store_and_canonical_client_id(monkeypatch, tmp_path):
    from services.execution.exchange_client import ExchangeClient

    captured = {}

    def _fake_place_order(ex, symbol, order_type, side, amount, price, params):
        captured["params"] = dict(params or {})
        return {"id": "ord-1"}

    monkeypatch.setattr(ExchangeClient, "build", lambda self: DummySuccessExchange())
    monkeypatch.setattr("services.execution.exchange_client.place_order", _fake_place_order)

    exec_db = str(tmp_path / "execution.sqlite")
    client = ExchangeClient("coinbase")

    out = client.submit_order(
        intent_id="intent-1",
        client_id=None,
        symbol="BTC/USD",
        side="buy",
        amount=1.0,
        price=1.0,
        order_type="limit",
        exec_db=exec_db,
    )

    expected_cid = canonical_make_client_order_id("coinbase", "intent-1")
    row = ExecutionOrderDedupeStore(exec_db=exec_db).get_by_intent("coinbase", "intent-1")

    assert out == {"id": "ord-1"}
    assert captured["params"]["clientOrderId"] == expected_cid
    assert row["client_order_id"] == expected_cid
    assert row["remote_order_id"] == "ord-1"
    assert row["status"] == "submitted"


def test_submit_order_passes_live_submit_owner_context_when_supported(monkeypatch, tmp_path):
    from services.execution.exchange_client import ExchangeClient

    captured = {}

    def _fake_place_order(ex, symbol, order_type, side, amount, price, params, context=None):
        captured["context"] = context
        return {"id": "ord-2"}

    monkeypatch.setattr(ExchangeClient, "build", lambda self: DummySuccessExchange())
    monkeypatch.setattr("services.execution.exchange_client.place_order", _fake_place_order)

    exec_db = str(tmp_path / "execution.sqlite")
    client = ExchangeClient("coinbase")

    out = client.submit_order(
        intent_id="intent-2",
        client_id=None,
        symbol="BTC/USD",
        side="buy",
        amount=1.0,
        price=1.0,
        order_type="limit",
        exec_db=exec_db,
    )

    assert out == {"id": "ord-2"}
    assert captured["context"] == ExecutionContext(
        mode="live",
        authority="LIVE_SUBMIT_OWNER",
        origin="exchange_client.submit_order",
    )
