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
    parser.add_argument(
        "--skip-ohlcv-preflight",
        action="store_true",
        help="skip live public-OHLCV reachability probe; intended for offline tests only",
    )
    args = parser.parse_args(argv)

    report = build_funding_stage0_readiness(run_ohlcv_preflight=not bool(args.skip_ohlcv_preflight))
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
