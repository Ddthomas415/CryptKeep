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

from services.analytics.research_artifact_inventory import build_research_artifact_inventory  # noqa: E402


def _print_report(payload: dict[str, Any]) -> None:
    print("=== Research Artifact Inventory ===")
    print(f"ok={bool(payload.get('ok'))} artifacts={payload.get('artifact_count')}")
    if payload.get("reason"):
        print(f"reason={payload.get('reason')}")
    if payload.get("lane_filter"):
        print(f"lane_filter={payload.get('lane_filter')}")
    if payload.get("artifact_id_filter"):
        print(f"artifact_id_filter={payload.get('artifact_id_filter')}")
    if payload.get("reason") == "invalid_artifact_id":
        available = ",".join(str(item) for item in list(payload.get("available_artifact_ids") or []))
        print(f"available_artifact_ids={available}")
    if payload.get("reason") == "invalid_lane":
        available = ",".join(str(item) for item in list(payload.get("available_lanes") or []))
        print(f"available_lanes={available}")
    summary = dict(payload.get("summary") or {})
    print(
        "summary: "
        f"found={summary.get('found', 0)} "
        f"missing={summary.get('missing', 0)} "
        f"latest_ok={summary.get('latest_ok', 0)} "
        f"latest_not_ok={summary.get('latest_not_ok', 0)} "
        f"unreadable={summary.get('unreadable', 0)} "
        f"action_required={summary.get('action_required', 0)}"
    )
    for row in list(payload.get("artifacts") or []):
        if not isinstance(row, dict):
            continue
        print(
            "- "
            f"{row.get('artifact_id')}: "
            f"status={row.get('latest_status')} "
            f"lane={row.get('lane')} "
            f"count={row.get('artifact_count')} "
            f"latest={row.get('latest_path') or '-'}"
        )
        if bool(row.get("action_required")):
            print(f"  reason={row.get('blocking_reason')}")
            print(f"  next_action={row.get('next_action')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inventory of accepted research artifacts and latest hashes. "
            "This does not run research, fetch market data, mutate artifacts, or "
            "produce campaign/promotion evidence."
        )
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--lane", default=None, help="Limit output to one research lane")
    parser.add_argument("--artifact-id", default=None, help="Limit output to one artifact_id")
    args = parser.parse_args(argv)

    payload = build_research_artifact_inventory(
        repo_root=ROOT,
        lane=args.lane,
        artifact_id=args.artifact_id,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
