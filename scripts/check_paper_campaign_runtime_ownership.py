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

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.analytics.paper_campaign_runtime_ownership import (  # noqa: E402
    build_paper_campaign_runtime_ownership_report,
    load_status_payload,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check captured laptop/Hetzner paper campaign status payloads for "
            "runtime duplicate ownership."
        ),
    )
    parser.add_argument(
        "--laptop-status-json",
        type=Path,
        required=True,
        help="Path to restore_paper_campaigns.py --status JSON from the laptop.",
    )
    parser.add_argument(
        "--hetzner-status-json",
        type=Path,
        required=True,
        help="Path to restore_paper_campaigns.py --status JSON from Hetzner.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, object]) -> None:
    print("=== Paper Campaign Runtime Ownership ===")
    print(f"status={report.get('status')}")
    print(f"ok={bool(report.get('ok'))}")
    print(f"read_only={bool(report.get('read_only'))}")
    print(f"restore_invoked={bool(report.get('restore_invoked'))}")
    print(f"ssh_invoked={bool(report.get('ssh_invoked'))}")
    for row in list(report.get("running_campaigns") or []):
        if not isinstance(row, dict):
            continue
        print(
            f"- {row.get('host')} running {row.get('name')} "
            f"session={row.get('session_strategy_id')} "
            f"state={row.get('normalized_state_dir')} pid={row.get('pid')}"
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
    try:
        report = build_paper_campaign_runtime_ownership_report(
            laptop_status=load_status_payload(args.laptop_status_json),
            hetzner_status=load_status_payload(args.hetzner_status_json),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report = {
            "ok": False,
            "status": "runtime_single_owner_blocked",
            "read_only": True,
            "restore_invoked": False,
            "ssh_invoked": False,
            "status_payload_only": True,
            "blockers": [f"invalid_status_payload:{type(exc).__name__}"],
            "recommendations": ["capture fresh laptop and Hetzner status JSON"],
        }

    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
