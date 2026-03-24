import pytest

from services.execution.order_reconciliation import SafeToRetryAfterReconciliation


class DummyStore:
    def __init__(self):
        self.claimed = []
        self.unknown = []
        self.submitted = []
        self.errors = []

    def claim(self, **kwargs):
        self.claimed.append(kwargs)
        return {"ok": True}

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


def test_ambiguous_submit_requires_reconciliation_before_retry(monkeypatch):
    from services.execution.exchange_client import ExchangeClient

    store = DummyStore()

    monkeypatch.setattr("services.execution.exchange_client.OrderDedupeStore", lambda *a, **k: store)
    monkeypatch.setattr("services.execution.exchange_client.load_exchange_credentials", lambda exchange_id: {"apiKey": "x"})
    monkeypatch.setattr(ExchangeClient, "build", lambda self: DummyExchange(RuntimeError("network timeout")))
    monkeypatch.setattr("services.execution.exchange_client.client_id_param", lambda exchange_id, client_id: {"clientOrderId": client_id})
    monkeypatch.setattr("services.execution.exchange_client._is_ambiguous_submit_error", lambda e: True)
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
        )

    assert len(store.unknown) == 1


def test_ambiguous_submit_allows_retry_only_when_confirmed_not_placed(monkeypatch):
    from services.execution.exchange_client import ExchangeClient

    store = DummyStore()

    monkeypatch.setattr("services.execution.exchange_client.OrderDedupeStore", lambda *a, **k: store)
    monkeypatch.setattr("services.execution.exchange_client.load_exchange_credentials", lambda exchange_id: {"apiKey": "x"})
    monkeypatch.setattr(ExchangeClient, "build", lambda self: DummyExchange(RuntimeError("network timeout")))
    monkeypatch.setattr("services.execution.exchange_client.client_id_param", lambda exchange_id, client_id: {"clientOrderId": client_id})
    monkeypatch.setattr("services.execution.exchange_client._is_ambiguous_submit_error", lambda e: True)
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
        )

    assert len(store.unknown) == 1
