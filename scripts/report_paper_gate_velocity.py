#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# CBP_BOOTSTRAP_SYS_PATH

try:
    from _bootstrap import add_repo_root_to_syspath  # noqa: E402
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath  # noqa: E402

add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.control.paper_gate_velocity import (  # noqa: E402
    build_paper_gate_velocity_report,
    write_paper_gate_velocity_artifact,
)


def _print_report(payload: dict[str, Any]) -> None:
    velocity = dict(payload.get("velocity") or {})
    bar_velocity = dict(payload.get("qualified_bar_velocity") or {})
    overall_velocity = dict(payload.get("overall_velocity") or {})
    trips = dict(payload.get("round_trips") or {})
    bars = dict(payload.get("qualified_bars") or {})
    days = dict(payload.get("days") or {})
    print("=== Paper Gate Velocity Report ===")
    print(f"Strategy: {payload.get('strategy_id')} target={payload.get('target_strategy')}")
    print(f"Policy: {payload.get('policy_id')} valid={payload.get('policy_valid')}")
    print(
        "Round trips: "
        f"qualified={trips.get('qualified', 0)} "
        f"required={trips.get('required', 0)} "
        f"remaining={trips.get('remaining', 0)} "
        f"all_history={trips.get('all_history', 0)} "
        f"excluded_all_history={trips.get('excluded_all_history', 0)}"
    )
    print(
        "Days: "
        f"recorded={days.get('recorded', 0)} "
        f"required={days.get('required', 0)} "
        f"remaining={days.get('remaining', 0)}"
    )
    if bars.get("enabled"):
        print(
            "Qualified bars: "
            f"recorded={bars.get('recorded', 0)} "
            f"required={bars.get('required', 0)} "
            f"remaining={bars.get('remaining', 0)} "
            f"source={bars.get('source')}"
        )
        print(
            "Qualified bar velocity: "
            f"status={bar_velocity.get('status')} "
            f"mean_days_per_bar={bar_velocity.get('mean_days_per_qualified_bar')} "
            f"estimated_days_remaining={bar_velocity.get('estimated_days_remaining')} "
            f"estimated_completion_ts={bar_velocity.get('estimated_completion_ts')}"
        )
    print(
        "Velocity: "
        f"status={velocity.get('status')} "
        f"mean_days_per_round_trip={velocity.get('mean_days_per_qualified_round_trip')} "
        f"estimated_days_remaining={velocity.get('estimated_days_remaining')} "
        f"estimated_completion_ts={velocity.get('estimated_completion_ts')}"
    )
    print(
        "Overall estimate: "
        f"status={overall_velocity.get('status')} "
        f"blocking_threshold={overall_velocity.get('blocking_threshold')} "
        f"estimated_days_remaining={overall_velocity.get('estimated_days_remaining')} "
        f"estimated_completion_ts={overall_velocity.get('estimated_completion_ts')}"
    )
    findings = list(payload.get("findings") or [])
    if findings:
        print("Findings:")
        for item in findings:
            print(f"- {item.get('severity')}: {item.get('id')} — {item.get('summary')}")
    print(payload.get("summary_text") or "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only paper promotion gate velocity and completion estimate"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--evidence-dest",
        default="",
        help="Write latest and stamped JSON artifacts into this directory",
    )
    args = parser.parse_args(argv)

    payload = build_paper_gate_velocity_report()
    if args.evidence_dest:
        payload["artifact_paths"] = write_paper_gate_velocity_artifact(
            payload,
            evidence_dest=args.evidence_dest,
        )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        _print_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
