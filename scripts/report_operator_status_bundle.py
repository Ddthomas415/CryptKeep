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

from services.analytics.operator_status_bundle import build_operator_status_bundle  # noqa: E402


def _print_report(payload: dict[str, Any]) -> None:
    summary = dict(payload.get("summary") or {})
    reports = dict(payload.get("reports") or {})
    actions_payload = dict(payload.get("actions") or {})
    section_filter = str(payload.get("section_filter") or "")
    filter_keys = (
        "backlog_lane_filter",
        "backlog_lane_ordinal_filter",
        "research_pipeline_filter",
        "research_artifact_lane_filter",
        "research_artifact_id_filter",
        "research_command_lane_filter",
        "research_command_input_class_filter",
        "research_command_id_filter",
        "operator_read_only_medium_lane_item_filter",
        "operator_read_only_command_id_filter",
        "operator_proof_category_filter",
        "operator_proof_line_filter",
        "operator_proof_passive_ordinal_filter",
    )
    print("=== Operator Status Bundle ===")
    print(f"ok={bool(payload.get('ok'))}")
    if payload.get("reason"):
        print(f"reason={payload.get('reason')}")
    source_reasons = dict(payload.get("source_reasons") or {})
    for key, value in sorted(source_reasons.items()):
        print(f"source_reason:{key}={value}")
    if section_filter:
        print(f"section_filter={section_filter}")
    for key in filter_keys:
        if payload.get(key):
            print(f"{key}={payload.get(key)}")
    shown = payload.get("shown_sections") or []
    if shown:
        print("shown_sections=" + ",".join(str(value) for value in shown))
    if "backlog_lane_status" in reports:
        print(
            "backlog: "
            f"passive={summary.get('passive_operator_items', 0)} "
            f"low={summary.get('low_risk_docs_tests', 0)} "
            f"medium={summary.get('medium_risk_runtime_read_only', 0)} "
            f"high={summary.get('high_risk_gate_execution_deploy', 0)} "
            f"actions_required={summary.get('backlog_lane_actions_required', 0)}"
        )
    for row in list(actions_payload.get("backlog_lanes") or [])[:5]:
        if not isinstance(row, dict):
            continue
        print(
            "backlog_action: "
            f"#{row.get('ordinal')} "
            f"{row.get('lane_key')} "
            f"action={row.get('next_action')}"
        )
    if "research_pipeline_status" in reports:
        print(
            "research: "
            f"wired={summary.get('research_pipelines_wired', 0)} "
            f"latest_ok={summary.get('research_pipelines_latest_ok', 0)} "
            f"not_run={summary.get('research_pipelines_not_run', 0)} "
            f"actions_required={summary.get('research_pipeline_actions_required', 0)}"
        )
    if "research_artifact_inventory" in reports:
        print(
            "research_artifacts: "
            f"found={summary.get('research_artifacts_found', 0)} "
            f"latest_ok={summary.get('research_artifacts_latest_ok', 0)} "
            f"missing={summary.get('research_artifacts_missing', 0)} "
            f"actions_required={summary.get('research_artifact_actions_required', 0)}"
        )
    for row in list(actions_payload.get("research_artifacts") or [])[:5]:
        if not isinstance(row, dict):
            continue
        print(
            "research_artifact_action: "
            f"{row.get('artifact_id')} "
            f"lane={row.get('lane')} "
            f"status={row.get('latest_status')} "
            f"reason={row.get('blocking_reason')} "
            f"action={row.get('next_action')}"
        )
    research_actions = list(actions_payload.get("research_pipelines") or [])
    for row in research_actions:
        if not isinstance(row, dict):
            continue
        print(
            "research_action: "
            f"{row.get('pipeline_id')} "
            f"status={row.get('latest_status')} "
            f"reason={row.get('blocking_reason')} "
            f"action={row.get('next_action')}"
        )
    if "research_command_status" in reports:
        print(
            "research_commands: "
            f"wired={summary.get('research_commands_wired', 0)} "
            f"not_wired={summary.get('research_commands_not_wired', 0)} "
            f"actions_required={summary.get('research_command_actions_required', 0)}"
        )
    for row in list(actions_payload.get("research_commands") or [])[:5]:
        if not isinstance(row, dict):
            continue
        print(
            "research_command_action: "
            f"{row.get('command_id')} "
            f"lane={row.get('lane')} "
            f"reason={row.get('blocking_reason')} "
            f"action={row.get('next_action')}"
        )
    if "operator_read_only_command_status" in reports:
        print(
            "operator_read_only_commands: "
            f"wired={summary.get('operator_read_only_commands_wired', 0)} "
            f"not_wired={summary.get('operator_read_only_commands_not_wired', 0)} "
            f"actions_required={summary.get('operator_read_only_command_actions_required', 0)}"
        )
    for row in list(actions_payload.get("operator_read_only_commands") or [])[:5]:
        if not isinstance(row, dict):
            continue
        print(
            "operator_read_only_command_action: "
            f"{row.get('command_id')} "
            f"lane_item={row.get('medium_lane_item')} "
            f"reason={row.get('blocking_reason')} "
            f"action={row.get('next_action')}"
        )
    if "operator_proof_status" in reports:
        print(
            "proofs: "
            f"remaining={summary.get('remaining_proof_or_coverage_markers', 0)} "
            f"host_side={summary.get('host_side_markers', 0)} "
            f"proof_ready={summary.get('proof_ready_markers', 0)} "
            f"actions_required={summary.get('operator_proof_actions_required', 0)}"
        )
    for row in list(actions_payload.get("passive_operator_evidence") or [])[:5]:
        if not isinstance(row, dict):
            continue
        print(
            "passive_action: "
            f"#{row.get('ordinal')} "
            f"action={row.get('next_action')}"
        )
    for row in list(actions_payload.get("operator_proofs") or [])[:5]:
        if not isinstance(row, dict):
            continue
        print(
            "proof_action: "
            f"L{row.get('line')} "
            f"{row.get('category')} "
            f"action={row.get('next_action')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only bundle of operator backlog, research, and proof status reports."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument(
        "--section",
        default=None,
        help=(
            "Limit output to one section: backlog, research_pipeline, research_artifact, "
            "research_command, operator_read_only, or operator_proof"
        ),
    )
    parser.add_argument("--backlog-lane", default=None, help="Forward a lane filter to backlog lane status")
    parser.add_argument(
        "--backlog-lane-ordinal",
        default=None,
        help="Limit backlog lane actions to one 1-based actionable item ordinal; requires --backlog-lane",
    )
    parser.add_argument(
        "--research-pipeline",
        default=None,
        help="Forward a pipeline_id filter to research pipeline status",
    )
    parser.add_argument(
        "--research-artifact-lane",
        default=None,
        help="Forward a lane filter to research artifact inventory",
    )
    parser.add_argument(
        "--research-artifact-id",
        default=None,
        help="Forward an artifact_id filter to research artifact inventory",
    )
    parser.add_argument(
        "--research-command-lane",
        default=None,
        help="Forward a lane filter to research command status",
    )
    parser.add_argument(
        "--research-command-input-class",
        default=None,
        help="Forward an input_class filter to research command status",
    )
    parser.add_argument(
        "--research-command-id",
        default=None,
        help="Forward a command_id filter to research command status",
    )
    parser.add_argument(
        "--operator-read-only-medium-lane-item",
        default=None,
        help="Forward a medium-lane-item filter to operator read-only command status",
    )
    parser.add_argument(
        "--operator-read-only-command-id",
        default=None,
        help="Forward a command_id filter to operator read-only command status",
    )
    parser.add_argument(
        "--operator-proof-category",
        default=None,
        help="Forward a category filter to operator proof status",
    )
    parser.add_argument(
        "--operator-proof-line",
        default=None,
        help="Forward a REMAINING_TASKS.md line filter to operator proof status",
    )
    parser.add_argument(
        "--operator-proof-passive-ordinal",
        default=None,
        help="Forward a passive operator-evidence 1-based ordinal filter to operator proof status",
    )
    args = parser.parse_args(argv)

    payload = build_operator_status_bundle(
        repo_root=ROOT,
        section=args.section,
        backlog_lane=args.backlog_lane,
        backlog_lane_ordinal=args.backlog_lane_ordinal,
        research_pipeline=args.research_pipeline,
        research_artifact_lane=args.research_artifact_lane,
        research_artifact_id=args.research_artifact_id,
        research_command_lane=args.research_command_lane,
        research_command_input_class=args.research_command_input_class,
        research_command_id=args.research_command_id,
        operator_read_only_medium_lane_item=args.operator_read_only_medium_lane_item,
        operator_read_only_command_id=args.operator_read_only_command_id,
        operator_proof_category=args.operator_proof_category,
        operator_proof_line=args.operator_proof_line,
        operator_proof_passive_ordinal=args.operator_proof_passive_ordinal,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
