from __future__ import annotations

from services.security import private_connectivity


class _FakeExchange:
    def __init__(self):
        self.closed = False

    def fetch_balance(self):
        return {"total": {"BTC": 1.0, "USD": 25.0}}

    def close(self):
        self.closed = True


def test_private_connectivity_uses_loader_and_closes_client(monkeypatch):
    fake_exchange = _FakeExchange()

    monkeypatch.setattr(
        private_connectivity,
        "load_exchange_credentials",
        lambda exchange: {"source": "keyring", "apiKey": "k", "secret": "s"},
    )
    monkeypatch.setattr(private_connectivity, "make_exchange", lambda exchange, creds: fake_exchange)

    out = private_connectivity.test_private_connectivity("coinbase")

    assert out["ok"] is True
    assert out["balance_total_asset_count"] == 2
    assert fake_exchange.closed is True


def test_private_connectivity_reports_missing_credentials_source(monkeypatch):
    monkeypatch.setattr(
        private_connectivity,
        "load_exchange_credentials",
        lambda exchange: {"source": "env", "apiKey": "", "secret": ""},
    )

    out = private_connectivity.test_private_connectivity("coinbase")

    assert out["ok"] is False
    assert out["reason"] == "missing_credentials"
    assert out["source"] == "env"
