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

from services.ai_copilot.operator_briefing import build_operator_briefing  # noqa: E402


def _print_report(payload: dict[str, Any]) -> None:
    print("=== Operator Briefing ===")
    print(
        f"ok={bool(payload.get('ok'))} "
        f"read_only={bool(payload.get('read_only'))} "
        f"advisory_only={bool(payload.get('advisory_only'))} "
        f"capital_authority={payload.get('capital_authority')}"
    )
    if payload.get("reason"):
        print(f"reason={payload.get('reason')}")
    for name, row in sorted(dict(payload.get("source_status") or {}).items()):
        print(f"source:{name} ok={bool(row.get('ok'))} status={row.get('status')}")
        if row.get("error_type"):
            print(f"  error={row.get('error_type')}:{row.get('error')}")

    summaries = dict(payload.get("summaries") or {})
    campaigns = dict(summaries.get("campaigns") or {})
    print(
        "campaigns="
        f"{campaigns.get('running_count', 0)}/{campaigns.get('campaign_count', 0)} "
        f"all_running={bool(campaigns.get('all_running'))}"
    )
    gate = dict(summaries.get("paper_gate") or {})
    round_trips = dict(gate.get("round_trips") or {})
    print(
        "paper_gate_round_trips="
        f"{round_trips.get('qualified', 0)}/{round_trips.get('required', 0)} "
        f"remaining={round_trips.get('remaining', 0)}"
    )
    cost = dict(summaries.get("cost_assumptions") or {})
    print(f"cost_assumptions={cost.get('overall', 'unknown')}")
    print("recommendations:")
    for idx, row in enumerate(list(payload.get("recommendations") or []), start=1):
        if not isinstance(row, dict):
            continue
        print(
            f"{idx}. priority={row.get('priority')} confidence={row.get('confidence')} "
            f"source={row.get('evidence_source')} action={row.get('action')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only advisory operator briefing over existing status reports."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument("--max-actions", type=int, default=8, help="Maximum next-action rows to include")
    args = parser.parse_args(argv)
    payload = build_operator_briefing(repo_root=ROOT, max_actions=args.max_actions)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
