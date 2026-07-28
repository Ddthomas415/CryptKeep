#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from scripts._bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parents[1])

from services.analytics.operator_next_actions import build_operator_next_actions  # noqa: E402


def _print_report(payload: dict[str, Any]) -> None:
    print("=== Operator Next Actions ===")
    print(
        f"ok={bool(payload.get('ok'))} "
        f"actions={payload.get('action_count_total', 0)} "
        f"shown={payload.get('action_count_returned', 0)}"
    )
    for key in (
        "lane_filter",
        "reason_filter",
        "action_source_filter",
        "backlog_lane_filter",
        "research_pipeline_filter",
        "research_command_lane_filter",
        "research_command_input_class_filter",
        "operator_proof_category_filter",
        "operator_proof_line_filter",
    ):
        value = payload.get(key)
        if value:
            print(f"{key}={value}")
    summary = dict(payload.get("summary") or {})
    for label, values in (
        ("by_lane", dict(summary.get("available_by_lane") or {})),
        ("by_reason", dict(summary.get("available_by_reason") or {})),
    ):
        if values:
            joined = " ".join(f"{key}={value}" for key, value in sorted(values.items()))
            print(f"{label}: {joined}")
    for idx, row in enumerate(list(payload.get("actions") or []), start=1):
        if not isinstance(row, dict):
            continue
        line = row.get("line")
        ref = f"L{line}" if line is not None else "-"
        print(
            f"{idx}. {row.get('lane')}:{row.get('source')} "
            f"ref={ref} reason={row.get('blocking_reason')} "
            f"action={row.get('next_action')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only compact next-action report from operator status."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument("--max-actions", type=int, default=20, help="Maximum actions to print or return")
    parser.add_argument(
        "--lane",
        choices=("research_pipeline", "operator_proof"),
        default=None,
        help="Limit output to one action lane",
    )
    parser.add_argument("--reason", default=None, help="Limit output to one blocking_reason value")
    parser.add_argument("--action-source", default=None, help="Limit output to one final action source value")
    parser.add_argument("--backlog-lane", default=None, help="Forward a backlog lane filter to the source bundle")
    parser.add_argument("--research-pipeline", default=None, help="Forward a research pipeline filter to the source bundle")
    parser.add_argument(
        "--research-command-lane",
        default=None,
        help="Forward a research command lane filter to the source bundle",
    )
    parser.add_argument(
        "--research-command-input-class",
        default=None,
        help="Forward a research command input-class filter to the source bundle",
    )
    parser.add_argument(
        "--operator-proof-category",
        default=None,
        help="Forward an operator proof category filter to the source bundle",
    )
    parser.add_argument(
        "--operator-proof-line",
        default=None,
        help="Forward a REMAINING_TASKS.md line filter to the source bundle",
    )
    args = parser.parse_args(argv)

    payload = build_operator_next_actions(
        repo_root=ROOT,
        max_actions=args.max_actions,
        lane=args.lane,
        reason=args.reason,
        action_source=args.action_source,
        backlog_lane=args.backlog_lane,
        research_pipeline=args.research_pipeline,
        research_command_lane=args.research_command_lane,
        research_command_input_class=args.research_command_input_class,
        operator_proof_category=args.operator_proof_category,
        operator_proof_line=args.operator_proof_line,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
