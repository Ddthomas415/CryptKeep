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

from services.analytics.hetzner_multi_venue_proposal_status import (  # noqa: E402
    build_hetzner_multi_venue_proposal_status,
    render_hetzner_multi_venue_proposal_status,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only status check for the disabled Hetzner Gate.io/Binance "
            "paper-research proposal manifest."
        )
    )
    parser.add_argument(
        "--manifest",
        default="configs/paper_evidence_campaigns.hetzner.multi_venue_proposed.json",
    )
    parser.add_argument("--preflight", action="store_true", help="Run read-only OHLCV preflights for candidate rows")
    parser.add_argument("--probe-limit", type=int, default=5)
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _exit_code(report: dict[str, object]) -> int:
    status = str(report.get("status") or "")
    if status in {"invalid_manifest", "invalid_candidate_rows"}:
        return 1
    if status == "preflight_failed":
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = build_hetzner_multi_venue_proposal_status(
        manifest_path=Path(args.manifest),
        run_preflight=bool(args.preflight),
        preflight_probe_limit=int(args.probe_limit),
        preflight_attempts=int(args.attempts),
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_hetzner_multi_venue_proposal_status(report))
    return _exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())

