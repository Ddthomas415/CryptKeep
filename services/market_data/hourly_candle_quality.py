"""R4 hourly-simulation diagnostics; no fetching, repairing or order submission."""
from __future__ import annotations

import math
import re

from services.execution.intent_ttl import _parse_created_epoch
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from storage.exit_event_journal import _decode_payload

HOUR_MS = 3_600_000
MAX_SNAPSHOT_BYTES = 1_048_576


def assess_hourly_candles(rows, *, now, timeframe="1h") -> dict:
    out = {"ok": False, "reason": "invalid_candles", "policy_version": 1, "timeframe": timeframe,
           "last_candle_open_ms": None, "last_candle_complete": None, "missing_hours": [],
           "current_hour_present": False, "window_hours": 60}
    epoch = _parse_created_epoch(now)
    if isinstance(now, bool) or epoch is None or not math.isfinite(epoch * 1000) or epoch < 0:
        return {**out, "reason": "invalid_clock"}
    if timeframe != "1h":
        return {**out, "reason": "not_hourly"}
    current = int(epoch * 1000) // HOUR_MS * HOUR_MS
    out["checked_epoch"] = epoch
    if not isinstance(rows, list) or not rows:
        return {**out, "reason": "no_candles"}
    indexed = {}
    previous = None
    for row in rows:
        try:
            if not isinstance(row, (list, tuple)) or len(row) < 6 or isinstance(row[0], bool):
                raise ValueError("invalid_row")
            stamp = float(row[0])
            if not math.isfinite(stamp) or stamp < 0 or stamp % HOUR_MS or stamp > current:
                raise ValueError("invalid_timestamp")
            stamp = int(stamp)
            if previous is not None and stamp <= previous:
                raise ValueError("unordered_or_duplicate")
            previous = stamp
            indexed[stamp] = row
        except (TypeError, ValueError, OverflowError):
            return out
    last = max(indexed)
    out.update(last_candle_open_ms=last, last_candle_complete=last + HOUR_MS <= epoch * 1000,
               current_hour_present=current in indexed)
    current_required = current in indexed or epoch - current / 1000 > 300
    end = current if current_required else current - HOUR_MS
    expected = range(end - 59 * HOUR_MS, end + HOUR_MS, HOUR_MS)
    missing = [stamp for stamp in expected if stamp not in indexed]
    out["missing_hours"] = missing
    if current not in indexed and epoch - current / 1000 > 300:
        return {**out, "reason": "current_hour_stale"}
    if missing:
        return {**out, "reason": "missing_hours"}
    for stamp in expected:
        row = indexed[stamp]
        try:
            if any(isinstance(value, bool) for value in row[1:6]):
                raise ValueError("invalid_price")
            opening, high, low, close, volume = map(float, row[1:6])
            if (not all(math.isfinite(value) for value in (opening, high, low, close, volume))
                    or min(opening, high, low, close) <= 0 or volume < 0
                    or high < max(opening, low, close) or low > min(opening, high, close)):
                raise ValueError("invalid_price")
        except (TypeError, ValueError, OverflowError):
            return {**out, "reason": "invalid_ohlcv"}
    return {**out, "ok": True, "reason": "fresh"}


def check_cached_hourly_candles(venue: str, symbol: str, *, clock, data_root=None) -> dict:
    from services.market_data.local_data_reader import _ohlcv_snapshot_path
    failure = {"ok": False, "reason": "cache_unreadable", "policy_version": 1}
    try:
        if not re.fullmatch(r"[a-z0-9_]+", normalize_venue(venue)) or "\\" in symbol or "\x00" in symbol:
            return {**failure, "reason": "invalid_market_identity"}
        path = _ohlcv_snapshot_path(venue, symbol, "1h")
        if data_root is not None:
            path = data_root / "snapshots" / path.name
        with path.open("rb") as stream:
            raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
        if len(raw) > MAX_SNAPSHOT_BYTES:
            return {**failure, "reason": "cache_too_large"}
        payload = _decode_payload(raw)
        if (not payload or payload.get("source") != "public_ohlcv"
                or normalize_venue(str(payload.get("venue", ""))) != normalize_venue(venue)
                or normalize_symbol(str(payload.get("symbol", ""))) != normalize_symbol(symbol)
                or payload.get("timeframe") != "1h"):
            return {**failure, "reason": "cache_identity_or_source_unverified"}
        return assess_hourly_candles(payload.get("candles"), now=clock())
    except Exception:
        return failure
