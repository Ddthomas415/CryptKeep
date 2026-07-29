from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.operator_status_bundle import build_operator_status_bundle


_ACTION_LANES: tuple[str, ...] = (
    "backlog_lane",
    "research_pipeline",
    "research_command",
    "passive_operator_evidence",
    "operator_proof",
)


def _backlog_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(dict(bundle.get("actions") or {}).get("backlog_lanes") or []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "lane": "backlog_lane",
                "source": str(row.get("lane_key") or ""),
                "line": None,
                "ordinal": row.get("ordinal"),
                "blocking_reason": "backlog_lane_item",
                "next_action": str(row.get("next_action") or ""),
            }
        )
    return rows


def _research_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(dict(bundle.get("actions") or {}).get("research_pipelines") or []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "lane": "research_pipeline",
                "source": str(row.get("pipeline_id") or ""),
                "line": None,
                "blocking_reason": row.get("blocking_reason"),
                "next_action": str(row.get("next_action") or ""),
            }
        )
    return rows


def _research_command_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(dict(bundle.get("actions") or {}).get("research_commands") or []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "lane": "research_command",
                "source": str(row.get("command_id") or ""),
                "line": None,
                "blocking_reason": row.get("blocking_reason"),
                "next_action": str(row.get("next_action") or ""),
            }
        )
    return rows


def _proof_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(dict(bundle.get("actions") or {}).get("operator_proofs") or []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "lane": "operator_proof",
                "source": str(row.get("category") or ""),
                "line": row.get("line"),
                "blocking_reason": row.get("category"),
                "next_action": str(row.get("next_action") or ""),
            }
        )
    return rows


def _passive_operator_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(dict(bundle.get("actions") or {}).get("passive_operator_evidence") or []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "lane": "passive_operator_evidence",
                "source": "passive_operator_evidence",
                "line": None,
                "ordinal": row.get("ordinal"),
                "blocking_reason": "passive_operator_evidence",
                "next_action": str(row.get("next_action") or ""),
            }
        )
    return rows


def _counts_by_key(actions: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in actions:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def build_operator_next_actions(
    *,
    repo_root: str | Path | None = None,
    max_actions: int = 20,
    lane: str | None = None,
    reason: str | None = None,
    action_source: str | None = None,
    backlog_lane: str | None = None,
    backlog_lane_ordinal: int | str | None = None,
    research_pipeline: str | None = None,
    research_command_lane: str | None = None,
    research_command_input_class: str | None = None,
    research_command_id: str | None = None,
    operator_proof_category: str | None = None,
    operator_proof_line: int | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    limit = max(1, int(max_actions))
    lane_filter = str(lane or "").strip()
    reason_filter = str(reason or "").strip()
    source_filter = str(action_source or "").strip()
    backlog_lane_filter = str(backlog_lane or "").strip()
    backlog_lane_ordinal_filter = str(backlog_lane_ordinal or "").strip()
    research_pipeline_filter = str(research_pipeline or "").strip()
    research_command_lane_filter = str(research_command_lane or "").strip()
    research_command_input_filter = str(research_command_input_class or "").strip()
    research_command_id_filter = str(research_command_id or "").strip()
    proof_category_filter = str(operator_proof_category or "").strip()
    proof_line_filter = str(operator_proof_line or "").strip()
    invalid_lane_filter = bool(lane_filter) and lane_filter not in _ACTION_LANES
    bundle = build_operator_status_bundle(
        repo_root=root,
        backlog_lane=backlog_lane_filter or None,
        backlog_lane_ordinal=backlog_lane_ordinal_filter or None,
        research_pipeline=research_pipeline_filter or None,
        research_command_lane=research_command_lane_filter or None,
        research_command_input_class=research_command_input_filter or None,
        research_command_id=research_command_id_filter or None,
        operator_proof_category=proof_category_filter or None,
        operator_proof_line=proof_line_filter or None,
    )
    summary = dict(bundle.get("summary") or {})
    actions = [
        *_backlog_actions(bundle),
        *_research_actions(bundle),
        *_research_command_actions(bundle),
        *_passive_operator_actions(bundle),
        *_proof_actions(bundle),
    ]
    source_action_lanes: set[str] = set()
    if backlog_lane_filter or backlog_lane_ordinal_filter:
        source_action_lanes.add("backlog_lane")
    if research_pipeline_filter:
        source_action_lanes.add("research_pipeline")
    if research_command_lane_filter or research_command_input_filter or research_command_id_filter:
        source_action_lanes.add("research_command")
    if proof_category_filter or proof_line_filter:
        source_action_lanes.add("operator_proof")
    if source_action_lanes and not lane_filter:
        actions = [row for row in actions if row.get("lane") in source_action_lanes]
    if invalid_lane_filter:
        actions = []
    elif lane_filter:
        actions = [row for row in actions if row.get("lane") == lane_filter]
    if reason_filter:
        actions = [row for row in actions if row.get("blocking_reason") == reason_filter]
    if source_filter:
        actions = [row for row in actions if row.get("source") == source_filter]
    required_total = (
        int(summary.get("backlog_lane_actions_required") or 0)
        + int(summary.get("research_pipeline_actions_required") or 0)
        + int(summary.get("research_command_actions_required") or 0)
        + int(summary.get("passive_operator_evidence_actions_required") or 0)
        + int(summary.get("operator_proof_actions_required") or 0)
    )
    if lane_filter == "backlog_lane":
        required_total = int(summary.get("backlog_lane_actions_required") or 0)
    elif lane_filter == "research_pipeline":
        required_total = int(summary.get("research_pipeline_actions_required") or 0)
    elif lane_filter == "research_command":
        required_total = int(summary.get("research_command_actions_required") or 0)
    elif lane_filter == "operator_proof":
        required_total = int(summary.get("operator_proof_actions_required") or 0)
    elif lane_filter == "passive_operator_evidence":
        required_total = int(summary.get("passive_operator_evidence_actions_required") or 0)
    elif source_action_lanes:
        required_total = 0
        if "backlog_lane" in source_action_lanes:
            required_total += int(summary.get("backlog_lane_actions_required") or 0)
        if "research_pipeline" in source_action_lanes:
            required_total += int(summary.get("research_pipeline_actions_required") or 0)
        if "research_command" in source_action_lanes:
            required_total += int(summary.get("research_command_actions_required") or 0)
        if "operator_proof" in source_action_lanes:
            required_total += int(summary.get("operator_proof_actions_required") or 0)
    if reason_filter:
        # The source summary has lane totals, not reason totals; once filtered
        # by reason, the truthful total is the filtered available row count.
        required_total = len(actions)
    if source_filter:
        # Source is a final action-row field, not a source-report summary
        # dimension, so the truthful total is the filtered available row count.
        required_total = len(actions)
    if required_total <= 0:
        required_total = len(actions)
    if invalid_lane_filter:
        required_total = 0

    return {
        "schema_version": 1,
        "report_type": "operator_next_actions",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": bool(bundle.get("ok")) and not invalid_lane_filter,
        "reason": "invalid_action_lane" if invalid_lane_filter else None,
        "read_only": True,
        "planning_only": True,
        "does_not_close_proof": True,
        "does_not_run_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "repo_root": str(root),
        "available_action_lanes": list(_ACTION_LANES),
        "lane_filter": lane_filter or None,
        "reason_filter": reason_filter or None,
        "action_source_filter": source_filter or None,
        "backlog_lane_filter": backlog_lane_filter or None,
        "backlog_lane_ordinal_filter": (
            int(backlog_lane_ordinal_filter) if backlog_lane_ordinal_filter.isdigit() else None
        ),
        "research_pipeline_filter": research_pipeline_filter or None,
        "research_command_lane_filter": research_command_lane_filter or None,
        "research_command_input_class_filter": research_command_input_filter or None,
        "research_command_id_filter": research_command_id_filter or None,
        "operator_proof_category_filter": proof_category_filter or None,
        "operator_proof_line_filter": int(proof_line_filter) if proof_line_filter.isdigit() else None,
        "source_reason": bundle.get("reason"),
        "source_reasons": dict(bundle.get("source_reasons") or {}),
        "source_report_type": bundle.get("report_type"),
        "source_summary": summary,
        "summary": {
            "available_by_lane": _counts_by_key(actions, "lane"),
            "available_by_reason": _counts_by_key(actions, "blocking_reason"),
        },
        "action_count_total": required_total,
        "action_count_available": len(actions),
        "action_count_returned": min(len(actions), limit),
        "actions": actions[:limit],
    }
