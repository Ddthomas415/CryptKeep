from __future__ import annotations

from services.backtest import ohlcv_archive as arch


def _bars(start_ms: int, count: int, step_ms: int = 3_600_000) -> list[list[float]]:
    return [
        [
            float(start_ms + (idx * step_ms)),
            100.0 + idx,
            101.0 + idx,
            99.0 + idx,
            100.5 + idx,
            10.0 + idx,
        ]
        for idx in range(count)
    ]


def _paged_fetcher(all_rows: list[list[float]]):
    def _fetch(_venue, _symbol, *, timeframe, limit, since_ms=None):
        del timeframe
        rows = [row for row in all_rows if since_ms is None or int(row[0]) >= int(since_ms)]
        return rows[: int(limit)]

    return _fetch


def test_paginate_walks_forward_across_pages():
    all_rows = _bars(1_700_000_000_000, 25)

    got = arch.paginate_ohlcv(
        _paged_fetcher(all_rows),
        venue="okx",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        since_ms=int(all_rows[0][0]),
        page_limit=10,
        max_pages=10,
        max_bars=1000,
    )

    assert len(got) == 25
    assert [row[0] for row in got] == sorted(row[0] for row in got)


def test_paginate_respects_max_bars_and_until():
    all_rows = _bars(1_700_000_000_000, 100)
    until = int(all_rows[20][0])

    capped = arch.paginate_ohlcv(
        _paged_fetcher(all_rows),
        venue="okx",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        since_ms=int(all_rows[0][0]),
        page_limit=10,
        max_pages=100,
        max_bars=30,
    )
    bounded = arch.paginate_ohlcv(
        _paged_fetcher(all_rows),
        venue="okx",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        since_ms=int(all_rows[0][0]),
        until_ms=until,
        page_limit=10,
        max_pages=100,
        max_bars=1000,
    )

    assert len(capped) == 30
    assert all(int(row[0]) <= until for row in bounded)


def test_paginate_terminates_on_empty_page():
    got = arch.paginate_ohlcv(
        lambda *args, **kwargs: [],
        venue="okx",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        since_ms=1_700_000_000_000,
        page_limit=10,
        max_pages=100,
        max_bars=1000,
    )

    assert got == []


def test_backfill_writes_idempotently_and_hashes_archive(tmp_path):
    db = tmp_path / "market_raw.sqlite"
    all_rows = _bars(1_700_000_000_000, 12)
    fetcher = _paged_fetcher(all_rows)

    first = arch.backfill_archive(
        fetcher,
        venue="okx",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        since_ms=int(all_rows[0][0]),
        page_limit=5,
        max_pages=10,
        max_bars=1000,
        db_path=db,
    )
    second = arch.backfill_archive(
        fetcher,
        venue="okx",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        since_ms=int(all_rows[0][0]),
        page_limit=5,
        max_pages=10,
        max_bars=1000,
        db_path=db,
    )
    loaded = arch.load_archived_ohlcv(
        "okx",
        "BTC/USDT:USDT",
        timeframe="1h",
        limit=12,
        db_path=db,
    )

    assert first["ok"] is True
    assert first["rows_written"] == 12
    assert second["dataset_hash"] == first["dataset_hash"]
    assert loaded["ok"] is True
    assert loaded["dataset_hash"] == first["dataset_hash"]


def test_fetch_with_meta_archive_carries_hash(tmp_path, monkeypatch):
    from services.backtest import signal_replay

    db = tmp_path / "market_raw.sqlite"
    all_rows = _bars(1_700_000_000_000, 20)
    arch.backfill_archive(
        _paged_fetcher(all_rows),
        venue="okx",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        since_ms=int(all_rows[0][0]),
        page_limit=20,
        max_pages=2,
        max_bars=1000,
        db_path=db,
    )
    monkeypatch.setenv("CBP_MARKET_ARCHIVE_DB", str(db))

    meta = signal_replay.fetch_ohlcv_with_meta("okx", "BTC/USDT:USDT", timeframe="1h", limit=20)

    assert meta["source"] == arch.ARCHIVE_SOURCE
    assert meta["dataset_hash"]
    assert meta["count"] == 20
    assert signal_replay.fetch_ohlcv("okx", "BTC/USDT:USDT", timeframe="1h", limit=20) == meta["rows"]
