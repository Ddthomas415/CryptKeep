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
from services.analytics.price_action_candidate_triage import (
    run_price_action_candidate_triage,
)
from services.backtest.price_action_context import (
    DEFAULT_DISPLACEMENT_BODY_FRACTION,
    DEFAULT_DISPLACEMENT_LOOKBACK,
    DEFAULT_DISPLACEMENT_RANGE_MULTIPLIER,
    DEFAULT_OPENING_RANGE_BARS,
    DEFAULT_SWING_LOOKBACK,
    DEFAULT_WICK_BODY_RATIO,
    DEFAULT_WICK_RANGE_RATIO,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write a research-only price-action candidate triage report from "
            "archived OHLCV. This ranks labels for manual review only; it does "
            "not change strategy config, campaigns, gates, promotion evidence, "
            "or execution."
        )
    )
    parser.add_argument("--venue", default="coinbase")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--since", default=None)
    parser.add_argument("--archive-db", type=Path, default=None)
    parser.add_argument("--window-bars", type=int, default=120)
    parser.add_argument("--step-bars", type=int, default=None)
    parser.add_argument("--min-windows", type=int, default=2)
    parser.add_argument("--horizon-bars", type=int, default=1)
    parser.add_argument("--min-labeled-rows", type=int, default=1)
    parser.add_argument("--fee-bps", type=float, default=None)
    parser.add_argument("--slippage-bps", type=float, default=None)
    parser.add_argument("--min-sample-size", type=int, default=10)
    parser.add_argument("--min-avg-delta-pct", type=float, default=0.0)
    parser.add_argument("--min-outperform-ratio", type=float, default=0.60)
    parser.add_argument("--max-underperform-ratio", type=float, default=0.40)
    parser.add_argument("--swing-lookback", type=int, default=DEFAULT_SWING_LOOKBACK)
    parser.add_argument(
        "--displacement-lookback",
        type=int,
        default=DEFAULT_DISPLACEMENT_LOOKBACK,
    )
    parser.add_argument(
        "--opening-range-bars",
        type=int,
        default=DEFAULT_OPENING_RANGE_BARS,
    )
    parser.add_argument("--wick-body-ratio", type=float, default=DEFAULT_WICK_BODY_RATIO)
    parser.add_argument("--wick-range-ratio", type=float, default=DEFAULT_WICK_RANGE_RATIO)
    parser.add_argument(
        "--displacement-range-multiplier",
        type=float,
        default=DEFAULT_DISPLACEMENT_RANGE_MULTIPLIER,
    )
    parser.add_argument(
        "--displacement-body-fraction",
        type=float,
        default=DEFAULT_DISPLACEMENT_BODY_FRACTION,
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--fail-if-not-ok", action="store_true")
    return parser.parse_args(argv)


def _label_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "swing_lookback": int(args.swing_lookback),
        "displacement_lookback": int(args.displacement_lookback),
        "opening_range_bars": int(args.opening_range_bars),
        "wick_body_ratio": float(args.wick_body_ratio),
        "wick_range_ratio": float(args.wick_range_ratio),
        "displacement_range_multiplier": float(args.displacement_range_multiplier),
        "displacement_body_fraction": float(args.displacement_body_fraction),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_price_action_candidate_triage(
        venue=str(args.venue),
        symbol=str(args.symbol),
        timeframe=str(args.timeframe),
        limit=int(args.limit),
        since_ms=parse_utc_ms(args.since),
        db_path=str(args.archive_db) if args.archive_db is not None else None,
        window_bars=int(args.window_bars),
        step_bars=int(args.step_bars) if args.step_bars is not None else None,
        min_windows=int(args.min_windows),
        horizon_bars=int(args.horizon_bars),
        min_labeled_rows=int(args.min_labeled_rows),
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        label_config=_label_config(args),
        min_sample_size=int(args.min_sample_size),
        min_avg_delta_pct=float(args.min_avg_delta_pct),
        min_outperform_ratio=float(args.min_outperform_ratio),
        max_underperform_ratio=float(args.max_underperform_ratio),
    )
    result["script"] = "scripts/research/run_price_action_candidate_triage.py"
    result["archive_db_arg"] = str(args.archive_db) if args.archive_db is not None else None
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
