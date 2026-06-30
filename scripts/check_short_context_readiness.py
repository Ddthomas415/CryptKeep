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

from services.analytics.short_context_readiness import (  # noqa: E402
    DEFAULT_REQUIRED_KINDS,
    build_short_context_readiness,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check read-only short/context data readiness from stored "
            "crypto-edge evidence."
        ),
    )
    parser.add_argument("--db-path", default="", help="Optional crypto-edge sqlite path override")
    parser.add_argument("--source", default="live_public", help="Snapshot source to inspect")
    parser.add_argument(
        "--required-kind",
        action="append",
        choices=["funding", "open_interest", "basis", "quotes", "order_book"],
        help="Required row family. Repeat to override the default required set.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, object]) -> None:
    print("=== Short Context Readiness ===")
    print(f"status={report.get('status')}")
    print(f"source={report.get('source_filter')}")
    print(f"replay_scope={report.get('replay_scope')}")
    print(f"live_public_replay_ready={bool(report.get('live_public_replay_ready'))}")
    print(f"fixture_replay_ready={bool(report.get('fixture_replay_ready'))}")
    print(f"research_only={bool(report.get('research_only'))}")
    print(f"execution_enabled={bool(report.get('execution_enabled'))}")
    families = list(report.get("row_families") or [])
    for row in families:
        if not isinstance(row, dict):
            continue
        marker = "required" if bool(row.get("required")) else "optional"
        print(
            f"- {row.get('kind')}: {row.get('reason')} "
            f"rows={row.get('row_count')} source={row.get('source')} {marker}"
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
    required = tuple(args.required_kind) if args.required_kind else DEFAULT_REQUIRED_KINDS
    report = build_short_context_readiness(
        db_path=str(args.db_path or ""),
        source=str(args.source or "live_public"),
        required_kinds=required,
    )
    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return 0 if bool(report.get("live_public_replay_ready")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
