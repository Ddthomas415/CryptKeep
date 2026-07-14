from __future__ import annotations

import math

import pytest

import services.backtest.signal_replay as signal_replay
from services.backtest.ohlcv_archive import (
    load_archived_ohlcv,
    ohlcv_dataset_hash,
)
from storage.market_store_sqlite import MarketStore


def _seed(store: MarketStore, *, ts_ms: int, close: float, symbol: str = "BTC/USD") -> None:
    store.upsert_ohlcv(
        ts_ms=ts_ms,
        exchange="coinbase",
        symbol=symbol,
        timeframe="1h",
        o=close - 1.0,
        h=close + 1.0,
        l=close - 2.0,
        cl=close,
        v=10.0,
    )


def test_market_store_load_ohlcv_latest_and_since(tmp_path):
    store = MarketStore(tmp_path / "archive.sqlite")
    _seed(store, ts_ms=1_700_000_000_000, close=100.0)
    _seed(store, ts_ms=1_700_000_003_600, close=101.0)
    _seed(store, ts_ms=1_700_000_007_200, close=102.0)

    latest = store.load_ohlcv(exchange="coinbase", symbol="BTC/USD", timeframe="1h", limit=2)
    assert [row[0] for row in latest] == [1_700_000_003_600, 1_700_000_007_200]
    assert [row[4] for row in latest] == [101.0, 102.0]

    since = store.load_ohlcv(
        exchange="coinbase",
        symbol="BTC/USD",
        timeframe="1h",
        limit=5,
        since_ms=1_700_000_003_600,
    )
    assert [row[0] for row in since] == [1_700_000_003_600, 1_700_000_007_200]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("o", math.nan, "invalid_market_ohlcv_numeric:o"),
        ("h", 99.0, "invalid_market_ohlcv_numeric:ohlcv_range"),
        ("l", 102.0, "invalid_market_ohlcv_numeric:ohlcv_range"),
        ("cl", 0.0, "invalid_market_ohlcv_numeric:price_nonpositive"),
        ("v", float("inf"), "invalid_market_ohlcv_numeric:v"),
        ("v", -1.0, "invalid_market_ohlcv_numeric:v_negative"),
    ],
)
def test_market_store_rejects_invalid_ohlcv_before_mutation(tmp_path, field, value, reason):
    store = MarketStore(tmp_path / "archive.sqlite")
    row = {
        "ts_ms": 1_700_000_000_000,
        "exchange": "coinbase",
        "symbol": "BTC/USD",
        "timeframe": "1h",
        "o": 100.0,
        "h": 102.0,
        "l": 99.0,
        "cl": 101.0,
        "v": 10.0,
    }
    row[field] = value

    with pytest.raises(ValueError, match=reason):
        store.upsert_ohlcv(**row)

    assert store.load_ohlcv(exchange="coinbase", symbol="BTC/USD", timeframe="1h", limit=10) == []


def test_market_store_rejects_invalid_ohlcv_timestamp_before_mutation(tmp_path):
    store = MarketStore(tmp_path / "archive.sqlite")

    with pytest.raises(ValueError, match="invalid_market_ohlcv_numeric:ts_ms"):
        store.upsert_ohlcv(
            ts_ms=0,
            exchange="coinbase",
            symbol="BTC/USD",
            timeframe="1h",
            o=100.0,
            h=102.0,
            l=99.0,
            cl=101.0,
            v=10.0,
        )

    assert store.load_ohlcv(exchange="coinbase", symbol="BTC/USD", timeframe="1h", limit=10) == []


def test_market_store_preserves_missing_ohlcv_volume(tmp_path):
    store = MarketStore(tmp_path / "archive.sqlite")

    store.upsert_ohlcv(
        ts_ms=1_700_000_000_000,
        exchange="coinbase",
        symbol="BTC/USD",
        timeframe="1h",
        o=100.0,
        h=102.0,
        l=99.0,
        cl=101.0,
        v=None,
    )

    assert store.load_ohlcv(exchange="coinbase", symbol="BTC/USD", timeframe="1h", limit=10) == [
        [1_700_000_000_000, 100.0, 102.0, 99.0, 101.0, None]
    ]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("bid", math.nan, "invalid_market_ticker_numeric:bid"),
        ("ask", float("inf"), "invalid_market_ticker_numeric:ask"),
        ("last", 0.0, "invalid_market_ticker_numeric:last_nonpositive"),
        ("base_vol", -1.0, "invalid_market_ticker_numeric:base_vol_negative"),
        ("quote_vol", float("nan"), "invalid_market_ticker_numeric:quote_vol"),
    ],
)
def test_market_store_rejects_invalid_ticker_fields_before_mutation(tmp_path, field, value, reason):
    store = MarketStore(tmp_path / "archive.sqlite")
    row = {
        "ts_ms": 1_700_000_000_000,
        "exchange": "coinbase",
        "symbol": "BTC/USD",
        "bid": 100.0,
        "ask": 101.0,
        "last": 100.5,
        "base_vol": 10.0,
        "quote_vol": 1_005.0,
    }
    row[field] = value

    with pytest.raises(ValueError, match=reason):
        store.upsert_ticker(**row)

    assert store.last_tickers(exchange="coinbase", symbol="BTC/USD", limit=10) == []


def test_market_store_rejects_invalid_ticker_timestamp_before_mutation(tmp_path):
    store = MarketStore(tmp_path / "archive.sqlite")

    with pytest.raises(ValueError, match="invalid_market_ticker_numeric:ts_ms"):
        store.upsert_ticker(
            ts_ms=0,
            exchange="coinbase",
            symbol="BTC/USD",
            bid=100.0,
            ask=101.0,
            last=100.5,
        )

    assert store.last_tickers(exchange="coinbase", symbol="BTC/USD", limit=10) == []


def test_market_store_rejects_crossed_ticker_before_mutation(tmp_path):
    store = MarketStore(tmp_path / "archive.sqlite")

    with pytest.raises(ValueError, match="invalid_market_ticker_numeric:crossed_bid_ask"):
        store.upsert_ticker(
            ts_ms=1_700_000_000_000,
            exchange="coinbase",
            symbol="BTC/USD",
            bid=102.0,
            ask=101.0,
            last=101.5,
        )

    assert store.last_tickers(exchange="coinbase", symbol="BTC/USD", limit=10) == []


def test_market_store_preserves_partial_ticker_fields(tmp_path):
    store = MarketStore(tmp_path / "archive.sqlite")

    store.upsert_ticker(
        ts_ms=1_700_000_000_000,
        exchange="coinbase",
        symbol="BTC/USD",
        bid=None,
        ask=None,
        last=100.5,
        base_vol=None,
        quote_vol=None,
    )

    assert store.last_tickers(exchange="coinbase", symbol="BTC/USD", limit=10) == [
        {
            "ts_ms": 1_700_000_000_000,
            "exchange": "coinbase",
            "symbol": "BTC/USD",
            "bid": None,
            "ask": None,
            "last": 100.5,
            "base_vol": None,
            "quote_vol": None,
        }
    ]


def test_signal_replay_fetch_ohlcv_uses_archive_without_exchange(monkeypatch, tmp_path):
    db = tmp_path / "archive.sqlite"
    store = MarketStore(db)
    _seed(store, ts_ms=1_700_000_000_000, close=100.0)
    _seed(store, ts_ms=1_700_000_003_600, close=101.0)
    _seed(store, ts_ms=1_700_000_007_200, close=102.0)
    monkeypatch.setenv("CBP_MARKET_ARCHIVE_DB", str(db))

    def _unexpected_exchange(*args, **kwargs):  # pragma: no cover - failure path
        raise AssertionError("archive-complete fetch should not touch exchange")

    monkeypatch.setattr(signal_replay, "make_exchange", _unexpected_exchange)

    rows = signal_replay.fetch_ohlcv("coinbase", "BTC/USD", timeframe="1h", limit=2)

    assert [row[0] for row in rows] == [1_700_000_003_600, 1_700_000_007_200]
    assert [row[4] for row in rows] == [101.0, 102.0]


def test_signal_replay_fetch_ohlcv_falls_back_when_archive_incomplete(monkeypatch, tmp_path):
    db = tmp_path / "archive.sqlite"
    store = MarketStore(db)
    _seed(store, ts_ms=1_000, close=100.0)
    monkeypatch.setenv("CBP_MARKET_ARCHIVE_DB", str(db))
    seen: dict[str, object] = {}

    class _FakeExchange:
        def fetch_ohlcv(self, symbol, **kwargs):
            seen["symbol"] = symbol
            seen.update(kwargs)
            return [[10_000, 1, 2, 3, 4, 5], [20_000, 2, 3, 4, 5, 6]]

        def close(self):
            seen["closed"] = True

    monkeypatch.setattr(signal_replay, "make_exchange", lambda *args, **kwargs: _FakeExchange())

    rows = signal_replay.fetch_ohlcv("coinbase", "BTC/USD", timeframe="1h", limit=2, since_ms=5_000)

    assert rows == [[10_000, 1, 2, 3, 4, 5], [20_000, 2, 3, 4, 5, 6]]
    assert seen["timeframe"] == "1h"
    assert seen["limit"] == 2
    assert seen["since"] == 5_000
    assert seen["closed"] is True


def test_archive_hash_is_stable_and_metadata_sensitive(tmp_path):
    db = tmp_path / "archive.sqlite"
    store = MarketStore(db)
    _seed(store, ts_ms=2, close=101.0)
    _seed(store, ts_ms=1, close=100.0)

    loaded = load_archived_ohlcv(
        "coinbase",
        "BTC/USD",
        timeframe="1h",
        limit=2,
        db_path=db,
    )
    assert loaded["ok"] is True
    assert loaded["source"] == "market_ohlcv_archive"

    same_rows_reordered = list(reversed(loaded["rows"]))
    assert loaded["dataset_hash"] == ohlcv_dataset_hash(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1h",
        rows=same_rows_reordered,
    )
    assert loaded["dataset_hash"] != ohlcv_dataset_hash(
        venue="coinbase",
        symbol="ETH/USD",
        timeframe="1h",
        rows=loaded["rows"],
    )
    assert loaded["dataset_hash"] != ohlcv_dataset_hash(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1h",
        rows=loaded["rows"],
        source="synthetic_evidence_window",
    )


def test_load_archived_ohlcv_reports_incomplete_without_exchange(tmp_path):
    db = tmp_path / "archive.sqlite"
    store = MarketStore(db)
    _seed(store, ts_ms=1_000, close=100.0)

    out = load_archived_ohlcv("coinbase", "BTC/USD", timeframe="1h", limit=2, db_path=db)

    assert out["ok"] is False
    assert out["complete"] is False
    assert out["reason"] == "archive_incomplete"
    assert out["count"] == 1
