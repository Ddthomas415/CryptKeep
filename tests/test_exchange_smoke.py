from __future__ import annotations

from services.diagnostics import exchange_smoke as es


class _FakeExchange:
    def fetch_ticker(self, _symbol):
        return {"last": 100.0}

    def fetch_order_book(self, _symbol, limit=10):
        return {"bids": [[99.0, 1.0]], "asks": [[101.0, 1.0]], "limit": limit}

    def close(self):
        return None


def test_run_exchange_smoke_happy_path(monkeypatch):
    monkeypatch.setattr(es, "_build_exchange", lambda exchange_id, sandbox: _FakeExchange())
    out = es.run_exchange_smoke(
        exchange_id="coinbase",
        symbol="BTC/USD",
        sandbox=True,
        include_orderbook=True,
        orderbook_limit=5,
    )
    assert out["ok"] is True
    names = [c["name"] for c in out["checks"]]
    assert names == ["build_exchange", "fetch_ticker", "fetch_order_book"]


def test_run_exchange_smoke_build_failure(monkeypatch):
    def _boom(exchange_id, sandbox):
        raise RuntimeError("bad creds")

    monkeypatch.setattr(es, "_build_exchange", _boom)
    out = es.run_exchange_smoke(exchange_id="coinbase", symbol="BTC/USD", sandbox=True)
    assert out["ok"] is False
    assert out["checks"][0]["name"] == "build_exchange"
    assert out["checks"][0]["ok"] is False
