#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import argparse
import json
import sys  # noqa: F401
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.analytics.paper_campaign_ownership import (  # noqa: E402
    DEFAULT_HETZNER_CONFIG,
    DEFAULT_LAPTOP_CONFIG,
    build_paper_campaign_ownership_report,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check laptop/Hetzner paper campaign ownership manifests.",
    )
    parser.add_argument("--laptop-config", type=Path, default=DEFAULT_LAPTOP_CONFIG)
    parser.add_argument("--hetzner-config", type=Path, default=DEFAULT_HETZNER_CONFIG)
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, object]) -> None:
    print("=== Paper Campaign Ownership ===")
    print(f"status={report.get('status')}")
    print(f"ok={bool(report.get('ok'))}")
    print(f"read_only={bool(report.get('read_only'))}")
    print(f"restore_invoked={bool(report.get('restore_invoked'))}")
    print(f"ssh_invoked={bool(report.get('ssh_invoked'))}")
    for row in list(report.get("campaigns") or []):
        if not isinstance(row, dict):
            continue
        print(
            f"- {row.get('host')} owns {row.get('name')} "
            f"session={row.get('session_strategy_id')} state={row.get('state_dir')}"
        )
    blockers = list(report.get("blockers") or [])
    if blockers:
        print("blockers:")
        for item in blockers:
            print(f"- {item}")
    recommendations = list(report.get("recommendations") or [])
    if recommendations:
        print("recommendations:")
        for item in recommendations:
            print(f"- {item}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = build_paper_campaign_ownership_report(
        laptop_config=args.laptop_config,
        hetzner_config=args.hetzner_config,
        repo_root=ROOT,
    )
    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
