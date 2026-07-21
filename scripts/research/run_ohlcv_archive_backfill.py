#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.research.run_archive_walk_forward import parse_utc_ms
from services.backtest.ohlcv_archive import backfill_archive
from services.market_data.symbol_router import map_symbol, normalize_symbol, normalize_venue
from services.security.exchange_factory import make_exchange


def fetch_public_ohlcv(
    venue: str,
    symbol: str,
    *,
    timeframe: str,
    limit: int,
    since_ms: int | None = None,
) -> list[list[Any]]:
    """Fetch public OHLCV directly from the exchange.

    This deliberately bypasses archive-backed replay helpers so backfill never
    reads from the archive it is populating.
    """
    venue_s = normalize_venue(venue)
    mapped_symbol = map_symbol(venue_s, normalize_symbol(symbol))
    ex = make_exchange(venue_s, {"apiKey": None, "secret": None}, enable_rate_limit=True)
    try:
        kwargs: dict[str, Any] = {"timeframe": str(timeframe), "limit": int(limit)}
        if since_ms is not None:
            kwargs["since"] = int(since_ms)
        return list(ex.fetch_ohlcv(mapped_symbol, **kwargs) or [])
    finally:
        try:
            close = getattr(ex, "close", None)
            if callable(close):
                close()
        except Exception:
            pass


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill the local market OHLCV archive from public exchange data. "
            "This writes only the archive sqlite DB and produces a dataset-hashed "
            "research artifact summary; it does not affect campaigns, gates, or trading."
        )
    )
    parser.add_argument("--venue", default="okx")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--since", required=True, help="UTC timestamp/date/ms lower bound for the backfill.")
    parser.add_argument("--until", default=None, help="Optional UTC timestamp/date/ms upper bound for the backfill.")
    parser.add_argument("--archive-db", type=Path, default=None, help="Optional market archive sqlite path.")
    parser.add_argument("--page-limit", type=int, default=500)
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--max-bars", type=int, default=50_000)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 if no rows were written.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    since_ms = parse_utc_ms(str(args.since))
    until_ms = parse_utc_ms(str(args.until)) if args.until is not None else None
    if since_ms is None:
        raise SystemExit("invalid --since timestamp")
    if until_ms is not None and until_ms < since_ms:
        raise SystemExit("invalid --until timestamp: before --since")

    result = backfill_archive(
        fetch_public_ohlcv,
        venue=str(args.venue),
        symbol=str(args.symbol),
        timeframe=str(args.timeframe),
        since_ms=int(since_ms),
        until_ms=until_ms,
        page_limit=int(args.page_limit),
        max_pages=int(args.max_pages),
        max_bars=int(args.max_bars),
        db_path=str(args.archive_db) if args.archive_db is not None else None,
    )
    result["artifact_type"] = "ohlcv_archive_backfill_v1"
    result["research_data_ingestion"] = True
    result["source"] = "public_exchange_ohlcv"
    result["since_ms"] = int(since_ms)
    result["until_ms"] = None if until_ms is None else int(until_ms)
    result["page_limit"] = int(args.page_limit)
    result["max_pages"] = int(args.max_pages)
    result["max_bars"] = int(args.max_bars)
    result["limitations"] = [
        "market_data_archive_only",
        "not_strategy_evidence",
        "not_promotion_evidence",
        "not_trading",
    ]
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.fail_if_not_ok and not bool(result.get("ok")):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
