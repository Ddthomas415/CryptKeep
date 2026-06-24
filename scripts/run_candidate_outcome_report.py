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

from services.signals.candidate_outcomes import (  # noqa: E402
    build_candidate_outcome_report,
    write_candidate_outcome_report,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a read-only candidate-vs-paper-outcome report.",
    )
    parser.add_argument("--limit", type=int, default=30, help="Max candidate snapshots to scan")
    parser.add_argument("--since", type=str, default=None, help="ISO date lower bound")
    parser.add_argument("--top-n", type=int, default=3, help="Top candidates per snapshot")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--no-write", action="store_true", help="Do not persist report artifacts")
    return parser.parse_args()


def _print_summary(report: dict) -> None:
    summary = dict(report.get("summary") or {})
    print("=== Candidate Outcome Report ===")
    print(f"status={report.get('status')}")
    print(f"snapshots_reviewed={summary.get('snapshots_reviewed')}")
    print(f"candidates_reviewed={summary.get('candidates_reviewed')}")
    print(f"candidates_with_outcome_data={summary.get('candidates_with_outcome_data')}")
    print(f"no_outcome_count={summary.get('no_outcome_count')}")

    top = dict(summary.get("top_rank") or {})
    non_top = dict(summary.get("non_top_rank") or {})
    print(
        "top_rank="
        f"closed:{top.get('closed_trades')} "
        f"net_pnl:{top.get('net_pnl')} "
        f"win_rate:{top.get('win_rate_pct')}"
    )
    print(
        "non_top_rank="
        f"closed:{non_top.get('closed_trades')} "
        f"net_pnl:{non_top.get('net_pnl')} "
        f"win_rate:{non_top.get('win_rate_pct')}"
    )

    paths = report.get("artifact_paths")
    if isinstance(paths, dict) and paths:
        print(f"artifact_latest={paths.get('latest')}")
        print(f"artifact_dated={paths.get('dated')}")


def main() -> int:
    args = _parse_args()
    report = build_candidate_outcome_report(
        limit=int(args.limit),
        since_ts=args.since,
        top_n=int(args.top_n),
    )
    if not args.no_write:
        report["artifact_paths"] = write_candidate_outcome_report(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
