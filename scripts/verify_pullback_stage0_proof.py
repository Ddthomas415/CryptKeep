#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import argparse
import json
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.analytics.pullback_stage0_proof_verifier import (  # noqa: E402
    build_pullback_stage0_baseline,
    build_pullback_stage0_verification,
    write_pullback_stage0_baseline,
    write_pullback_stage0_verification,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record or verify the read-only pullback Stage 0 proof evidence.",
    )
    parser.add_argument(
        "--record-baseline",
        action="store_true",
        help="Record canonical/challenger counts before the 15-minute Stage 0 proof.",
    )
    parser.add_argument("--baseline", type=Path, default=None, help="Optional baseline JSON path")
    parser.add_argument(
        "--expected-commit",
        default="",
        help="Expected proof commit; defaults to HEAD",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--no-write", action="store_true", help="Do not persist report artifacts")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, object]) -> None:
    print("=== Pullback Stage 0 Proof Verifier ===")
    print(f"report_type={report.get('report_type')}")
    print(f"status={report.get('status', 'baseline_recorded')}")
    print(f"read_only={bool(report.get('read_only'))}")
    print(f"strategy={report.get('strategy')}")
    print(f"session_strategy_id={report.get('session_strategy_id')}")
    print(f"expected_commit={report.get('expected_commit')}")
    blocking = report.get("blocking_checks")
    if isinstance(blocking, list):
        print(f"blocking_checks={len(blocking)}")
    paths = report.get("artifact_paths")
    if isinstance(paths, dict) and paths:
        print(f"artifact_latest_json={paths.get('latest_json')}")
        print(f"artifact_latest_markdown={paths.get('latest_markdown')}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if bool(args.record_baseline):
        report = build_pullback_stage0_baseline(
            repo_root=ROOT,
            expected_commit=str(args.expected_commit or ""),
        )
        if not bool(args.no_write):
            report["artifact_paths"] = write_pullback_stage0_baseline(report)
        exit_code = 0
    else:
        report = build_pullback_stage0_verification(
            repo_root=ROOT,
            baseline_path=args.baseline,
            expected_commit=str(args.expected_commit or ""),
        )
        if not bool(args.no_write):
            report["artifact_paths"] = write_pullback_stage0_verification(report)
        exit_code = 0 if bool(report.get("passed")) else 1

    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
