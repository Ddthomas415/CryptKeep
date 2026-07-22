#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.research.run_archive_walk_forward import parse_utc_ms
from services.analytics.price_action_context_labels import run_archive_price_action_context_labels


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build research-only OHLCV price-action context labels from the "
            "market archive. Labels are descriptive context features only, not "
            "strategy config, campaign evidence, or promotion evidence."
        )
    )
    parser.add_argument("--venue", default="coinbase")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--since", default=None)
    parser.add_argument("--archive-db", type=Path, default=None)
    parser.add_argument("--swing-lookback", type=int, default=5)
    parser.add_argument("--range-lookback", type=int, default=10)
    parser.add_argument("--opening-range-bars", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 if labels cannot be built.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_archive_price_action_context_labels(
        venue=str(args.venue),
        symbol=str(args.symbol),
        timeframe=str(args.timeframe),
        limit=int(args.limit),
        since_ms=parse_utc_ms(args.since),
        db_path=args.archive_db,
        swing_lookback=int(args.swing_lookback),
        range_lookback=int(args.range_lookback),
        opening_range_bars=int(args.opening_range_bars),
    )
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
