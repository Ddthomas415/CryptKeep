from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from services.market_data.symbol_router import map_symbol, normalize_symbol, normalize_venue
from services.os.app_paths import data_dir
from storage.market_store_sqlite import MarketStore


ARCHIVE_SOURCE = "market_ohlcv_archive"


def default_archive_db_path() -> Path:
    raw = str(os.environ.get("CBP_MARKET_ARCHIVE_DB") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (data_dir() / "market_raw.sqlite").resolve()


def normalize_ohlcv_rows(rows: list[list[Any]]) -> list[list[Any]]:
    by_ts: dict[int, list[Any]] = {}
    for row in rows or []:
        if len(row) < 5:
            continue
        try:
            ts = int(float(row[0]))
            if ts < 10_000_000_000:
                ts *= 1000
            o = float(row[1])
            h = float(row[2])
            l = float(row[3])
            c = float(row[4])
            vol = None if len(row) < 6 or row[5] is None else float(row[5])
        except Exception:
            continue
        if ts <= 0 or not all(math.isfinite(v) for v in (o, h, l, c)):
            continue
        if vol is not None and not math.isfinite(vol):
            vol = None
        by_ts[ts] = [ts, o, h, l, c, vol]
    return [by_ts[ts] for ts in sorted(by_ts)]


def ohlcv_dataset_hash(
    *,
    venue: str,
    symbol: str,
    timeframe: str,
    rows: list[list[Any]],
    source: str = ARCHIVE_SOURCE,
) -> str:
    payload = {
        "source": str(source or ARCHIVE_SOURCE),
        "venue": normalize_venue(venue),
        "symbol": normalize_symbol(symbol),
        "timeframe": str(timeframe),
        "rows": normalize_ohlcv_rows(rows),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _symbol_candidates(venue: str, canonical_symbol: str) -> list[str]:
    v = normalize_venue(venue)
    original = str(canonical_symbol)
    normalized = normalize_symbol(original)
    mapped = map_symbol(v, normalized)
    out: list[str] = []
    for candidate in (mapped, normalized, original):
        if candidate and candidate not in out:
            out.append(candidate)
    return out


def load_archived_ohlcv(
    venue: str,
    canonical_symbol: str,
    *,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(db_path).expanduser().resolve() if db_path is not None else default_archive_db_path()
    requested_limit = max(1, int(limit))
    if not path.exists():
        return {
            "ok": False,
            "complete": False,
            "reason": "archive_missing",
            "archive_path": str(path),
            "rows": [],
        }

    exchange = normalize_venue(venue)
    store = MarketStore(path)
    for stored_symbol in _symbol_candidates(exchange, canonical_symbol):
        rows = normalize_ohlcv_rows(
            store.load_ohlcv(
                exchange=exchange,
                symbol=stored_symbol,
                timeframe=str(timeframe),
                limit=requested_limit,
                since_ms=since_ms,
            )
        )
        if not rows:
            continue
        complete = len(rows) >= requested_limit
        return {
            "ok": complete,
            "complete": complete,
            "reason": "ok" if complete else "archive_incomplete",
            "source": ARCHIVE_SOURCE,
            "archive_path": str(path),
            "exchange": exchange,
            "stored_symbol": stored_symbol,
            "symbol": normalize_symbol(canonical_symbol),
            "timeframe": str(timeframe),
            "count": len(rows),
            "requested_limit": requested_limit,
            "dataset_hash": ohlcv_dataset_hash(
                venue=exchange,
                symbol=canonical_symbol,
                timeframe=str(timeframe),
                rows=rows,
            ),
            "rows": rows,
        }

    return {
        "ok": False,
        "complete": False,
        "reason": "archive_no_rows",
        "archive_path": str(path),
        "exchange": exchange,
        "symbol": normalize_symbol(canonical_symbol),
        "timeframe": str(timeframe),
        "rows": [],
    }


def _row_ts_ms(row: list[Any]) -> int | None:
    if not isinstance(row, (list, tuple)) or not row:
        return None
    try:
        ts = int(float(row[0]))
    except Exception:
        return None
    if ts <= 0:
        return None
    if ts < 10_000_000_000:
        ts *= 1000
    return ts


def paginate_ohlcv(
    fetcher: Any,
    *,
    venue: str,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int | None = None,
    page_limit: int = 500,
    max_pages: int = 50,
    max_bars: int = 50_000,
) -> list[list[Any]]:
    cursor = int(since_ms)
    rows: list[list[Any]] = []
    page_size = max(1, int(page_limit))
    max_page_count = max(1, int(max_pages))
    max_row_count = max(1, int(max_bars))

    for _page in range(max_page_count):
        batch = fetcher(
            venue,
            symbol,
            timeframe=str(timeframe),
            limit=page_size,
            since_ms=cursor,
        )
        clean = normalize_ohlcv_rows(list(batch or []))
        if not clean:
            break
        rows = normalize_ohlcv_rows(rows + clean)
        if len(rows) >= max_row_count:
            rows = rows[:max_row_count]
            break
        last_ts = _row_ts_ms(rows[-1])
        if last_ts is None:
            break
        if until_ms is not None and last_ts >= int(until_ms):
            break
        next_cursor = int(last_ts) + 1
        if next_cursor <= cursor:
            break
        cursor = next_cursor

    if until_ms is not None:
        rows = [row for row in rows if (_row_ts_ms(row) or 0) <= int(until_ms)]
    return normalize_ohlcv_rows(rows)


def backfill_archive(
    fetcher: Any,
    *,
    venue: str,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int | None = None,
    page_limit: int = 500,
    max_pages: int = 50,
    max_bars: int = 50_000,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(db_path).expanduser().resolve() if db_path is not None else default_archive_db_path()
    exchange = normalize_venue(venue)
    stored_symbol = map_symbol(exchange, normalize_symbol(symbol))
    rows = paginate_ohlcv(
        fetcher,
        venue=exchange,
        symbol=symbol,
        timeframe=str(timeframe),
        since_ms=int(since_ms),
        until_ms=until_ms,
        page_limit=page_limit,
        max_pages=max_pages,
        max_bars=max_bars,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    store = MarketStore(path)
    written = 0
    for row in rows:
        ts = _row_ts_ms(row)
        if ts is None:
            continue
        vol = row[5] if len(row) > 5 else None
        store.upsert_ohlcv(
            ts_ms=ts,
            exchange=exchange,
            symbol=stored_symbol,
            timeframe=str(timeframe),
            o=float(row[1]),
            h=float(row[2]),
            l=float(row[3]),
            cl=float(row[4]),
            v=None if vol is None else float(vol),
        )
        written += 1

    return {
        "ok": written > 0,
        "archive_path": str(path),
        "exchange": exchange,
        "stored_symbol": stored_symbol,
        "symbol": normalize_symbol(symbol),
        "timeframe": str(timeframe),
        "rows_written": int(written),
        "dataset_hash": ohlcv_dataset_hash(
            venue=exchange,
            symbol=symbol,
            timeframe=str(timeframe),
            rows=rows,
        ),
    }
