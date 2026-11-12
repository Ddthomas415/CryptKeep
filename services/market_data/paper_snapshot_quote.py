"""Strict paper-only quote policy. Freshness is local receipt age, not book age."""
import math
import os
import re
import stat

from services.execution.intent_ttl import _parse_created_epoch
from services.market_data import tick_reader
from services.market_data.symbol_router import normalize_symbol, normalize_venue
from storage.exit_event_journal import _decode_payload

MAX_AGE_MS = 5000
MAX_SNAPSHOT_BYTES = 1_048_576
MAX_UTC_MS = 253_402_300_799_999
QUOTE_REASONS = frozenset({
    "ok", "missing_quote", "unverified_source", "wrong_market", "invalid_mapped_symbol",
    "unverified_ticker_symbol", "invalid_timestamp", "invalid_clock", "future_quote", "stale_quote",
    "invalid_book", "invalid_quote_value", "invalid_snapshot", "ambiguous_quote", "snapshot_unreadable",
    "observation_failed",
})
QUOTE_SOURCES = frozenset({"public_ticker", "sample_ohlcv", "unverified_ticker", "unknown"})


def _timestamp(value):
    return type(value) is int and 0 < value <= MAX_UTC_MS


def _market(venue, symbol):
    if type(venue) is not str or type(symbol) is not str:
        return None
    venue, symbol = normalize_venue(venue), normalize_symbol(symbol)
    if not venue or not symbol:
        return None
    return venue, symbol


def assess_paper_quote(quote, *, venue, symbol, now):
    """Return a fixed-shape receipt or a reason; recheck the same quote at fill."""
    if not isinstance(quote, dict):
        return None, "missing_quote"
    if quote.get("source") != "public_ticker":
        return None, "unverified_source"
    market = _market(venue, symbol)
    if market is None or _market(quote.get("venue"), quote.get("symbol")) != market:
        return None, "wrong_market"
    mapped = quote.get("symbol_mapped")
    if type(mapped) is not str or not re.fullmatch(r"[A-Za-z0-9._:/+-]{1,160}", mapped):
        return None, "invalid_mapped_symbol"
    returned = quote.get("ticker_symbol")
    if type(returned) is not str or normalize_symbol(returned) != normalize_symbol(mapped):
        return None, "unverified_ticker_symbol"
    snapshot_ms, received_ms = quote.get("snapshot_ts_ms"), quote.get("ts_ms")
    if not _timestamp(snapshot_ms) or not _timestamp(received_ms) or received_ms < snapshot_ms:
        return None, "invalid_timestamp"
    try:
        epoch = None if isinstance(now, bool) else _parse_created_epoch(now)
        if epoch is None or not 0 < epoch * 1000 <= MAX_UTC_MS:
            return None, "invalid_clock"
        now_ms = epoch * 1000
        if received_ms > now_ms:
            return None, "future_quote"
        if now_ms - snapshot_ms > MAX_AGE_MS or now_ms - received_ms > MAX_AGE_MS:
            return None, "stale_quote"
        bid, ask = quote.get("bid"), quote.get("ask")
        if (type(bid) not in (int, float) or type(ask) not in (int, float)
                or not math.isfinite(bid) or not math.isfinite(ask) or not 0 < bid <= ask):
            return None, "invalid_book"
    except (TypeError, ValueError, OverflowError, OSError):
        return None, "invalid_quote_value"
    exchange_ms = quote.get("exchange_ts_ms")
    return {
        "version": 1, "source": "public_ticker", "venue": market[0], "symbol": market[1],
        "symbol_mapped": mapped, "ticker_symbol": normalize_symbol(returned),
        "snapshot_ts_ms": snapshot_ms, "ts_ms": received_ms,
        "exchange_ts_ms": exchange_ms if _timestamp(exchange_ms) else None,
        "bid": float(bid), "ask": float(ask), "mid": bid + (ask - bid) / 2.0,
    }, None


def paper_quote_fill_price(quote, *, side, order_type, limit, slippage_bps):
    """Use the existing paper price model with an already validated quote."""
    if side not in ("buy", "sell"):
        return None
    try:
        if order_type == "limit":
            if type(limit) not in (int, float) or not math.isfinite(limit) or limit <= 0:
                return None
            if side == "buy":
                return quote["ask"] if limit >= quote["ask"] else None
            return quote["bid"] if limit <= quote["bid"] else None
        if (order_type != "market" or type(slippage_bps) not in (int, float)
                or not 0 <= slippage_bps < 10000):
            return None
        direction = 1 if side == "buy" else -1
        price = quote["mid"] * (1.0 + direction * slippage_bps / 10000.0)
        return price if math.isfinite(price) and price > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _quote_observation(tick, snapshot_ms, now):
    source = tick.get("source")
    bid, ask = tick.get("bid"), tick.get("ask")

    def positive(value):
        try:
            return type(value) in (int, float) and math.isfinite(value) and value > 0
        except OverflowError:
            return False

    epoch = None if isinstance(now, bool) else _parse_created_epoch(now)
    now_ms = epoch * 1000 if epoch is not None else None

    def age(stamp):
        return now_ms - stamp if now_ms is not None and 0 < now_ms <= MAX_UTC_MS and _timestamp(stamp) else None

    return {
        "source": source if type(source) is str and source in QUOTE_SOURCES else "unknown",
        "bid_present": bid is not None, "ask_present": ask is not None,
        "zero_price": any(type(value) in (int, float) and value == 0 for value in (bid, ask)),
        "invalid_price": (any(value is not None and not positive(value) for value in (bid, ask))
                          or (positive(bid) and positive(ask) and bid > ask)),
        "quote_age_ms": age(tick.get("ts_ms")), "snapshot_age_ms": age(snapshot_ms),
    }


def assess_paper_snapshot(snapshot, *, venue, symbol, clock, observation=None, require_canonical_mapping=False):
    """Assess one exact-market row from an already decoded snapshot."""
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("ticks"), list):
        return None, "invalid_snapshot"
    market = _market(venue, symbol)
    ticks = [tick for tick in snapshot["ticks"] if isinstance(tick, dict) and market is not None
             and _market(tick.get("venue"), tick.get("symbol")) == market]
    if len(ticks) != 1:
        return None, "ambiguous_quote" if ticks else "missing_quote"
    if require_canonical_mapping:
        mapped = ticks[0].get("symbol_mapped")
        if type(mapped) is not str or normalize_symbol(mapped) != market[1]:
            return None, "wrong_market"
    try:
        now = clock()
    except Exception:
        return None, "invalid_clock"
    if observation is not None:
        observation.update(_quote_observation(ticks[0], snapshot.get("ts_ms"), now))
    return assess_paper_quote(
        {**ticks[0], "snapshot_ts_ms": snapshot.get("ts_ms")},
        venue=venue, symbol=symbol, now=now,
    )


def read_paper_quote(venue, symbol, *, clock, observation=None):
    try:
        if observation is None:
            with tick_reader.LATEST.open("rb") as stream:
                raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
        else:
            # Recording must not wait on a pipe or follow a replacement symlink.
            fd = os.open(tick_reader.LATEST, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    return None, "invalid_snapshot"
                raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
        snapshot = _decode_payload(raw) if len(raw) <= MAX_SNAPSHOT_BYTES else None
        return assess_paper_snapshot(snapshot, venue=venue, symbol=symbol, clock=clock, observation=observation)
    except (OSError, ValueError, TypeError, OverflowError):
        return None, "snapshot_unreadable"


def observe_paper_quote(venue, symbol, *, clock):
    """Observe the public snapshot without conferring any order authority."""
    observation = {
        "source": "unknown", "quote_age_ms": None, "snapshot_age_ms": None,
        "bid_present": None, "ask_present": None, "zero_price": None, "invalid_price": None,
    }
    try:
        quote, reason = read_paper_quote(venue, symbol, clock=clock, observation=observation)
    except Exception:
        quote, reason = None, "observation_failed"
    return {**observation, "ok": quote is not None, "reason": reason or "ok"}
