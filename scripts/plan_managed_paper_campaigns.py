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

from services.analytics.managed_paper_campaign_planner import (  # noqa: E402
    DEFAULT_CANDIDATE_ARTIFACT,
    DEFAULT_CANDIDATE_OUTCOMES_ARTIFACT,
    DEFAULT_HETZNER_MANIFEST,
    DEFAULT_LAPTOP_MANIFEST,
    DEFAULT_SIGNAL_QUALITY_ARTIFACT,
    build_managed_paper_campaign_plan,
    write_managed_paper_campaign_plan,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a read-only managed paper-campaign proposal report.",
    )
    parser.add_argument("--host", choices=["laptop", "hetzner", "neither"], default="neither")
    parser.add_argument("--min-score", type=float, default=50.0)
    parser.add_argument("--max-candidates", type=int, default=5)
    parser.add_argument("--laptop-config", type=Path, default=DEFAULT_LAPTOP_MANIFEST)
    parser.add_argument("--hetzner-config", type=Path, default=DEFAULT_HETZNER_MANIFEST)
    parser.add_argument("--candidate-artifact", type=Path, default=DEFAULT_CANDIDATE_ARTIFACT)
    parser.add_argument(
        "--candidate-outcomes-artifact",
        type=Path,
        default=DEFAULT_CANDIDATE_OUTCOMES_ARTIFACT,
    )
    parser.add_argument("--signal-quality-artifact", type=Path, default=DEFAULT_SIGNAL_QUALITY_ARTIFACT)
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--no-write", action="store_true", help="Do not persist proposal artifacts")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, object]) -> None:
    summary = dict(report.get("summary") or {})
    print("=== Managed Paper Campaign Planner ===")
    print(f"status={report.get('status')}")
    print(f"read_only={bool(report.get('read_only'))}")
    print(f"candidate_evidence_status={report.get('candidate_evidence_status')}")
    print(f"existing_campaigns={summary.get('existing_campaigns')}")
    print(f"candidate_rows_reviewed={summary.get('candidate_rows_reviewed')}")
    print(f"proposal_count={summary.get('proposal_count')}")
    print(f"rejected_count={summary.get('rejected_count')}")
    paths = report.get("artifact_paths")
    if isinstance(paths, dict) and paths:
        print(f"artifact_latest_json={paths.get('latest_json')}")
        print(f"artifact_latest_markdown={paths.get('latest_markdown')}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = build_managed_paper_campaign_plan(
        repo_root=ROOT,
        laptop_manifest=args.laptop_config,
        hetzner_manifest=args.hetzner_config,
        candidate_artifact=args.candidate_artifact,
        candidate_outcomes_artifact=args.candidate_outcomes_artifact,
        signal_quality_artifact=args.signal_quality_artifact,
        proposal_host=str(args.host),
        min_score=float(args.min_score),
        max_candidates=int(args.max_candidates),
    )
    if not bool(args.no_write):
        report["artifact_paths"] = write_managed_paper_campaign_plan(report)

    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
