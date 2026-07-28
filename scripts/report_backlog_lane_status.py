#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from scripts._bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parents[1])

from services.analytics.backlog_lane_status import build_backlog_lane_status  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Report backlog execution-lane status without changing backlog state.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    args = parser.parse_args()

    out = build_backlog_lane_status(repo_root=ROOT)
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print("=== Backlog Lane Status ===")
        print(f"ok={bool(out.get('ok'))} lanes={out.get('lane_count')} items={out.get('total_item_count')}")
        summary = dict(out.get("summary") or {})
        print(
            "summary: "
            f"passive={summary.get('passive_operator_evidence')} "
            f"low={summary.get('low_risk_docs_tests')} "
            f"medium={summary.get('medium_risk_runtime_read_only')} "
            f"high={summary.get('high_risk_gate_execution_deploy')}"
        )
        for lane in list(out.get("lanes") or []):
            print(f"- {lane.get('name')}: {lane.get('item_count')}")
        missing = list(out.get("missing_lanes") or [])
        if missing:
            print("missing_lanes=" + ",".join(str(item) for item in missing))
    return 0 if bool(out.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
