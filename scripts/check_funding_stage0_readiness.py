#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.analytics.funding_stage0_readiness import (  # noqa: E402
    build_funding_stage0_readiness,
    write_funding_stage0_readiness,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only readiness report for the funding_extreme Stage 0 proof.")
    parser.add_argument("--json", action="store_true", help="print JSON and do not write artifacts")
    parser.add_argument("--symbol", default="", help="OHLCV/tick symbol for the Stage 0 paper run")
    parser.add_argument("--venue", default="", help="OHLCV/tick venue for the Stage 0 paper run")
    parser.add_argument("--signal-source", default="", help="signal source, expected form public_ohlcv_<timeframe>")
    parser.add_argument("--strategy-context-symbol", default="", help="funding context symbol, e.g. BTC/USDT:USDT")
    parser.add_argument("--strategy-context-venue", default="", help="funding context venue, e.g. okx")
    parser.add_argument("--strategy-context-source", default="", help="funding context source, default live_public")
    parser.add_argument(
        "--skip-ohlcv-preflight",
        action="store_true",
        help="skip live public-OHLCV reachability probe; intended for offline tests only",
    )
    args = parser.parse_args(argv)

    report = build_funding_stage0_readiness(
        run_ohlcv_preflight=not bool(args.skip_ohlcv_preflight),
        symbol=args.symbol,
        venue=args.venue,
        signal_source=args.signal_source,
        context_symbol=args.strategy_context_symbol,
        context_venue=args.strategy_context_venue,
        context_source=args.strategy_context_source,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        report["artifact_paths"] = write_funding_stage0_readiness(report)
        print("=== Funding Extreme Stage 0 Readiness ===")
        print(f"report_type={report['report_type']}")
        print(f"status={report['status']}")
        print(f"read_only={report['read_only']}")
        print(f"strategy={report['strategy']}")
        print(f"session_strategy_id={report['session_strategy_id']}")
        print(f"blocking_checks={len(report['blocking_checks'])}")
        print(f"stage0_command={report['proof_command']['shell']}")
        print(f"artifact_latest_json={report['artifact_paths']['latest_json']}")
        print(f"artifact_latest_markdown={report['artifact_paths']['latest_markdown']}")
    return 0 if bool(report.get("ready")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
