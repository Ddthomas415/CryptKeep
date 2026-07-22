#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.analytics.crypto_edge_research_pipeline import run_crypto_edge_research_pipeline


def _csv_floats(value: str) -> list[float]:
    out: list[float] = []
    for part in str(value or "").split(","):
        item = part.strip()
        if item:
            out.append(float(item))
    return out


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the research-only crypto-edge pipeline: funding replay, "
            "funding/price join, and threshold sensitivity. This does not "
            "fetch live data, change strategy config, start campaigns, or "
            "produce promotion evidence."
        )
    )
    parser.add_argument("--edge-db", type=Path, default=None)
    parser.add_argument("--archive-db", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--context-source", default="live_public")
    parser.add_argument("--context-venue", default="okx")
    parser.add_argument("--context-symbol", default="BTC/USDT:USDT")
    parser.add_argument("--price-venue", default="okx")
    parser.add_argument("--price-symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--funding-limit", type=int, default=500)
    parser.add_argument("--ohlcv-limit", type=int, default=500)
    parser.add_argument("--horizon-bars", type=int, default=1)
    parser.add_argument("--min-rows", type=int, default=1)
    parser.add_argument("--min-joined-rows", type=int, default=1)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--long-thresholds-pct", default="0.005,0.01,0.02,0.05")
    parser.add_argument("--short-thresholds-pct", default="-0.005,-0.01,-0.02,-0.05")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 if any pipeline stage is not ok.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_crypto_edge_research_pipeline(
        edge_db_path=args.edge_db,
        archive_db_path=args.archive_db,
        output_dir=args.output_dir,
        context_source=str(args.context_source),
        context_venue=str(args.context_venue),
        context_symbol=str(args.context_symbol),
        price_venue=str(args.price_venue),
        price_symbol=str(args.price_symbol),
        timeframe=str(args.timeframe),
        funding_limit=int(args.funding_limit),
        ohlcv_limit=int(args.ohlcv_limit),
        horizon_bars=int(args.horizon_bars),
        min_rows=int(args.min_rows),
        min_joined_rows=int(args.min_joined_rows),
        fee_bps=float(args.fee_bps),
        slippage_bps=float(args.slippage_bps),
        long_thresholds_pct=_csv_floats(args.long_thresholds_pct),
        short_thresholds_pct=_csv_floats(args.short_thresholds_pct),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.fail_if_not_ok and not bool(result.get("ok")):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
