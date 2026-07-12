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

from services.analytics.funding_stage0_proof_verifier import (  # noqa: E402
    build_funding_stage0_baseline,
    build_funding_stage0_verification,
    write_funding_stage0_baseline,
    write_funding_stage0_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record or verify read-only funding_extreme Stage 0 proof evidence.")
    parser.add_argument("--record-baseline", action="store_true", help="record canonical/challenger counts before the 15-minute Stage 0 proof")
    parser.add_argument("--baseline-path", default="", help="optional baseline JSON path override")
    parser.add_argument("--expected-commit", default="", help="expected short commit; defaults to current HEAD or baseline")
    parser.add_argument("--json", action="store_true", help="print JSON and do not write artifacts")
    args = parser.parse_args(argv)

    if args.record_baseline:
        report = build_funding_stage0_baseline(expected_commit=args.expected_commit)
        if not args.json:
            report["artifact_paths"] = write_funding_stage0_baseline(report)
    else:
        report = build_funding_stage0_verification(
            baseline_path=Path(args.baseline_path) if args.baseline_path else None,
            expected_commit=args.expected_commit,
        )
        if not args.json:
            report["artifact_paths"] = write_funding_stage0_verification(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print("=== Funding Extreme Stage 0 Proof Verifier ===")
        print(f"report_type={report['report_type']}")
        print(f"status={report.get('status', 'baseline_recorded')}")
        print(f"read_only={report['read_only']}")
        print(f"strategy={report['strategy']}")
        print(f"session_strategy_id={report['session_strategy_id']}")
        print(f"expected_commit={report['expected_commit']}")
        print(f"blocking_checks={len(report.get('blocking_checks') or [])}")
        if report.get("artifact_paths"):
            print(f"artifact_latest_json={report['artifact_paths']['latest_json']}")
            print(f"artifact_latest_markdown={report['artifact_paths']['latest_markdown']}")

    if args.record_baseline:
        return 0
    return 0 if bool(report.get("passed")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
