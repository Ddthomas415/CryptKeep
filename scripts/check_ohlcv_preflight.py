#!/usr/bin/env python3
"""Read-only public-OHLCV reachability preflight."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.execution.ohlcv_preflight import check_ohlcv_reachable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check public-OHLCV reachability before a governed Stage 0 run")
    parser.add_argument("--venue", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--signal-source", required=True, help="Expected form: public_ohlcv_<timeframe>")
    parser.add_argument("--probe-limit", type=int, default=5)
    parser.add_argument("--attempts", type=int, default=1, help="retry count for network/source failures")
    parser.add_argument("--attempt-delay-sec", type=float, default=0.0, help="optional delay between retry attempts")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = check_ohlcv_reachable(
        venue=args.venue,
        symbol=args.symbol,
        signal_source=args.signal_source,
        probe_limit=args.probe_limit,
        attempts=args.attempts,
        attempt_delay_sec=args.attempt_delay_sec,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        line = f"OHLCV preflight {str(result['status']).upper()} - {result['venue']} {result['symbol']}"
        if result.get("timeframe"):
            line += f" {result['timeframe']}"
        if result.get("row_count"):
            line += f" ({result['row_count']} rows)"
        if result.get("error"):
            line += f" - {result['error']}"
        elif result.get("reason"):
            line += f" - {result['reason']}"
        print(line)

    if bool(result.get("ok")):
        return 0
    if result.get("status") == "ohlcv_source_unreachable":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
