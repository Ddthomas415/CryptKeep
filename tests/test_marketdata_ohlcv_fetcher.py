from __future__ import annotations

import services.market_data.ohlcv_fetcher as ohlcv_fetcher


def test_fetch_ohlcv_delegates(monkeypatch):
    seen: dict = {}

    def _fake_fetch(venue, symbol, timeframe="1h", limit=500):
        seen["venue"] = venue
        seen["symbol"] = symbol
        seen["timeframe"] = timeframe
        seen["limit"] = limit
        return [[1, 2, 3, 4, 5, 6]]

    monkeypatch.setattr(ohlcv_fetcher, "_fetch_ohlcv", _fake_fetch)
    rows = ohlcv_fetcher.fetch_ohlcv("coinbase", "BTC/USD", timeframe="5m", limit=123)
    assert rows == [[1, 2, 3, 4, 5, 6]]
    assert seen == {"venue": "coinbase", "symbol": "BTC/USD", "timeframe": "5m", "limit": 123}


def test_fetch_payload_and_alias(monkeypatch):
    monkeypatch.setattr(
        ohlcv_fetcher,
        "_fetch_ohlcv",
        lambda venue, symbol, timeframe="1h", limit=500: [[10, 1, 2, 3, 4, 5], [20, 2, 3, 4, 5, 6]],
    )
    req = ohlcv_fetcher.OHLCVFetchRequest(venue="coinbase", symbol="ETH/USD", timeframe="1m", limit=2)
    out = ohlcv_fetcher.fetch(req)
    assert out["ok"] is True
    assert out["count"] == 2
    assert out["symbol"] == "ETH/USD"
    assert ohlcv_fetcher.load_ohlcv("coinbase", "ETH/USD", timeframe="1m", limit=2) == out["rows"]

