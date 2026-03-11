import asyncio

from shared.clients import exchange_client as ec


class _Resp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http_{self.status_code}")

    def json(self):
        return self._payload


class _Client:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        if "exchange.coinbase.com" in url:
            return _Resp({"price": "145.20", "bid": "145.10", "ask": "145.30"})
        return _Resp({"data": {"amount": "145.20"}})


class _Httpx:
    AsyncClient = _Client


def test_coinbase_snapshot_prefers_exchange_ticker(monkeypatch):
    monkeypatch.setattr(ec, "httpx", _Httpx)
    snap = asyncio.run(ec.fetch_coinbase_snapshot("SOL-USD", timeout=0.5, retries=0))

    assert snap["symbol"] == "SOL-USD"
    assert snap["exchange"] == "coinbase"
    assert snap["last_price"] == "145.20"
    assert snap["bid"] == "145.10"
    assert snap["ask"] == "145.30"
    assert snap["raw"]["provider"] == "coinbase_exchange"


def test_coinbase_snapshot_falls_back_when_httpx_missing(monkeypatch):
    monkeypatch.setattr(ec, "httpx", None)
    snap = asyncio.run(ec.fetch_coinbase_snapshot("SOL-USD", timeout=0.5, retries=0))

    assert snap["symbol"] == "SOL-USD"
    assert snap["exchange"] == "coinbase"
    assert snap["raw"]["source"] == "fallback"
    assert snap["raw"]["error"] == "httpx_missing"
