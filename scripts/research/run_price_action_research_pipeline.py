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
from services.analytics.price_action_research_pipeline import run_price_action_research_pipeline


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the research-only price-action pipeline: archive labels, "
            "forward returns, and window stability. This does not change "
            "strategies, campaigns, gates, or runtime config."
        )
    )
    parser.add_argument("--venue", default="coinbase")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--since", default=None)
    parser.add_argument("--archive-db", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--swing-lookback", type=int, default=5)
    parser.add_argument("--range-lookback", type=int, default=10)
    parser.add_argument("--opening-range-bars", type=int, default=3)
    parser.add_argument("--horizon-bars", type=int, default=1)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--forward-min-label-count", type=int, default=5)
    parser.add_argument("--min-forward-rows", type=int, default=1)
    parser.add_argument("--window-size-rows", type=int, default=100)
    parser.add_argument("--stability-min-windows", type=int, default=3)
    parser.add_argument("--stability-min-label-count", type=int, default=5)
    parser.add_argument("--consistency-threshold", type=float, default=0.6)
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 if any pipeline stage is not ok.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_price_action_research_pipeline(
        venue=str(args.venue),
        symbol=str(args.symbol),
        timeframe=str(args.timeframe),
        limit=int(args.limit),
        since_ms=parse_utc_ms(args.since),
        db_path=args.archive_db,
        output_dir=args.output_dir,
        swing_lookback=int(args.swing_lookback),
        range_lookback=int(args.range_lookback),
        opening_range_bars=int(args.opening_range_bars),
        horizon_bars=int(args.horizon_bars),
        fee_bps=float(args.fee_bps),
        slippage_bps=float(args.slippage_bps),
        forward_min_label_count=int(args.forward_min_label_count),
        min_forward_rows=int(args.min_forward_rows),
        window_size_rows=int(args.window_size_rows),
        stability_min_windows=int(args.stability_min_windows),
        stability_min_label_count=int(args.stability_min_label_count),
        consistency_threshold=float(args.consistency_threshold),
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.fail_if_not_ok and not bool(result.get("ok")):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
