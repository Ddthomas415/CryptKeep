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

from services.analytics.operator_read_only_command_status import (  # noqa: E402
    build_operator_read_only_command_status,
)


def _print_report(payload: dict[str, Any]) -> None:
    print("=== Operator Read-Only Command Status ===")
    print(f"ok={bool(payload.get('ok'))} commands={payload.get('command_count')}")
    if payload.get("medium_lane_item_filter"):
        print(f"medium_lane_item_filter={payload.get('medium_lane_item_filter')}")
    if payload.get("command_id_filter"):
        print(f"command_id_filter={payload.get('command_id_filter')}")
    if payload.get("reason"):
        print(f"reason={payload.get('reason')}")
    summary = dict(payload.get("summary") or {})
    print(f"summary: wired={summary.get('wired', 0)} not_wired={summary.get('not_wired', 0)}")
    by_lane_item = dict(summary.get("by_medium_lane_item") or {})
    if by_lane_item:
        print(
            "medium_lane_items: "
            + " ".join(f"{key}={value}" for key, value in sorted(by_lane_item.items()))
        )
    by_input = dict(summary.get("by_input_class") or {})
    if by_input:
        print("inputs: " + " ".join(f"{key}={value}" for key, value in sorted(by_input.items())))
    for row in list(payload.get("commands") or []):
        if not isinstance(row, dict):
            continue
        state = "ok" if bool(row.get("wiring_ok")) else "not_wired"
        print(
            "- "
            f"{row.get('command_id')}: {state} "
            f"lane_item={row.get('medium_lane_item')} "
            f"input={row.get('input_class')} "
            f"make={row.get('make_target') or '-'}"
        )
        reasons = [str(item) for item in list(row.get("reasons") or []) if str(item)]
        if reasons:
            print(f"  reasons={','.join(reasons)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only status report for medium-lane operator command wiring."
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--medium-lane-item", default=None, help="Limit output to one medium lane item")
    parser.add_argument("--command-id", default=None, help="Limit output to one command_id")
    args = parser.parse_args(argv)

    payload = build_operator_read_only_command_status(
        repo_root=ROOT,
        medium_lane_item=args.medium_lane_item,
        command_id=args.command_id,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
