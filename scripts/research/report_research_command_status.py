#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# CBP_BOOTSTRAP_SYS_PATH

try:
    from scripts._bootstrap import add_repo_root_to_syspath  # noqa: E402
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts._bootstrap import add_repo_root_to_syspath  # noqa: E402

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parents[2])

from services.analytics.research_command_status import build_research_command_status  # noqa: E402


def _print_report(payload: dict[str, Any]) -> None:
    print("=== Research Command Status ===")
    print(f"ok={bool(payload.get('ok'))} commands={payload.get('command_count')}")
    if payload.get("lane_filter"):
        print(f"lane_filter={payload.get('lane_filter')}")
    if payload.get("input_class_filter"):
        print(f"input_class_filter={payload.get('input_class_filter')}")
    summary = dict(payload.get("summary") or {})
    print(f"summary: wired={summary.get('wired', 0)} not_wired={summary.get('not_wired', 0)}")
    by_lane = dict(summary.get("by_lane") or {})
    print(
        "lanes: "
        f"archive={by_lane.get('archive', 0)} "
        f"funding={by_lane.get('funding', 0)} "
        f"price_action={by_lane.get('price_action', 0)} "
        f"status={by_lane.get('status', 0)}"
    )
    by_input = dict(summary.get("by_input_class") or {})
    print(
        "inputs: "
        f"none={by_input.get('none', 0)} "
        f"archive={by_input.get('archive_input', 0)} "
        f"artifact={by_input.get('artifact_input', 0)} "
        f"state={by_input.get('state_input', 0)} "
        f"operator_args={by_input.get('operator_args', 0)}"
    )
    for row in list(payload.get("commands") or []):
        if not isinstance(row, dict):
            continue
        state = "ok" if bool(row.get("wiring_ok")) else "not_wired"
        print(
            "- "
            f"{row.get('command_id')}: {state} "
            f"lane={row.get('lane')} "
            f"input={row.get('input_class')} "
            f"make={row.get('make_target') or '-'}"
        )
        reasons = [str(item) for item in list(row.get("reasons") or []) if str(item)]
        if reasons:
            print(f"  reasons={','.join(reasons)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only status report for accepted research command wiring and input classes."
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--lane", default=None, help="Limit output to one command lane")
    parser.add_argument("--input-class", default=None, help="Limit output to one input_class")
    args = parser.parse_args(argv)

    payload = build_research_command_status(
        repo_root=ROOT,
        lane=args.lane,
        input_class=args.input_class,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
