from __future__ import annotations

from services.analytics import crypto_edge_collector as collector


class _FakeExchange:
    def __init__(self, *, venue: str) -> None:
        self.venue = venue
        self.closed = False

    def load_markets(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True

    def fetch_funding_rate(self, symbol: str) -> dict:
        return {"symbol": symbol, "fundingRate": 0.00025}

    def fetch_ticker(self, symbol: str) -> dict:
        mapping = {
            "BTC/USDT": {"bid": 84000.0, "ask": 84010.0, "last": 84005.0},
            "BTC/USDT:USDT": {"bid": 84050.0, "ask": 84060.0, "last": 84055.0},
        }
        return dict(mapping.get(symbol, {"bid": 100.0, "ask": 101.0, "last": 100.5}))

    def fetch_order_book(self, symbol: str, limit: int = 5) -> dict:
        if self.venue == "coinbase":
            return {"bids": [[84010.0, 1.0]], "asks": [[84015.0, 1.0]]}
        return {"bids": [[84020.0, 1.0]], "asks": [[84005.0, 1.0]]}


def test_collect_live_crypto_edge_snapshot_builds_research_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        collector,
        "_open_public_exchange",
        lambda venue: _FakeExchange(venue=str(venue)),
    )

    out = collector.collect_live_crypto_edge_snapshot(
        {
            "funding": [{"venue": "binance", "symbol": "BTC/USDT:USDT", "interval_hours": 8.0}],
            "basis": [{"venue": "binance", "spot_symbol": "BTC/USDT", "perp_symbol": "BTC/USDT:USDT", "days_to_expiry": 7}],
            "quotes": [{"venue": "coinbase", "symbol": "BTC/USD"}, {"venue": "kraken", "symbol": "BTC/USD"}],
        }
    )

    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["execution_enabled"] is False
    assert len(out["funding_rows"]) == 1
    assert out["funding_rows"][0]["funding_rate"] == 0.00025
    assert len(out["basis_rows"]) == 1
    assert out["basis_rows"][0]["spot_px"] > 0.0
    assert len(out["quote_rows"]) == 2
    assert all(check["ok"] is True for check in out["checks"])


def test_collect_live_crypto_edge_snapshot_reports_unsupported_funding(monkeypatch) -> None:
    class _NoFundingExchange(_FakeExchange):
        fetch_funding_rate = None  # type: ignore[assignment]

    monkeypatch.setattr(
        collector,
        "_open_public_exchange",
        lambda venue: _NoFundingExchange(venue=str(venue)),
    )

    out = collector.collect_live_crypto_edge_snapshot(
        {
            "funding": [{"venue": "binance", "symbol": "BTC/USDT:USDT"}],
            "basis": [],
            "quotes": [],
        }
    )

    assert out["funding_rows"] == []
    assert out["checks"] == [
        {
            "kind": "funding",
            "venue": "binance",
            "symbol": "BTC/USDT:USDT",
            "ok": False,
            "reason": "funding_unsupported",
        }
    ]
