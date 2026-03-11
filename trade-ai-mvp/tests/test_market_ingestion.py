import asyncio

from shared.clients.exchange_client import fetch_coinbase_snapshot


def test_market_snapshot_client_returns_shape_even_on_fallback():
    data = asyncio.run(fetch_coinbase_snapshot("SOL-USD", timeout=0.001, retries=0))
    assert "symbol" in data
    assert "exchange" in data
    assert "last_price" in data
    assert "bid" in data
    assert "ask" in data
    assert "spread" in data
    assert "timestamp" in data
