from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.operator_status_bundle import build_operator_status_bundle


_ACTION_LANES: tuple[str, ...] = (
    "roadmap_tracking",
    "backlog_lane",
    "research_pipeline",
    "research_artifact",
    "research_command",
    "operator_read_only_command",
    "passive_operator_evidence",
    "operator_proof",
)

_SOURCE_ACTION_LANE_TO_SECTION = {
    "roadmap_tracking": "roadmap",
    "backlog_lane": "backlog",
    "research_pipeline": "research_pipeline",
    "research_artifact": "research_artifact",
    "research_command": "research_command",
    "operator_read_only_command": "operator_read_only",
    "passive_operator_evidence": "operator_proof",
    "operator_proof": "operator_proof",
}


def _roadmap_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(dict(bundle.get("actions") or {}).get("roadmap_tracking") or []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "lane": "roadmap_tracking",
                "source": "roadmap_tracking_status",
                "line": None,
                "blocking_reason": row.get("blocking_reason"),
                "next_action": str(row.get("next_action") or ""),
            }
        )
    return rows


def _backlog_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    # Backlog-lane rows are planning selectors, not concrete work. They remain
    # exposed separately so operators can inspect lanes without inflating the
    # executable next-action queue.
    return []


def _backlog_planning_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
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


def _research_artifact_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(dict(bundle.get("actions") or {}).get("research_artifacts") or []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "lane": "research_artifact",
                "source": str(row.get("artifact_id") or ""),
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


def _operator_read_only_command_actions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(dict(bundle.get("actions") or {}).get("operator_read_only_commands") or []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "lane": "operator_read_only_command",
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
        artifact_payload = row.get("artifact_status") or {}
        artifact_status = artifact_payload if isinstance(artifact_payload, dict) else {}
        rows.append(
            {
                "lane": "passive_operator_evidence",
                "source": "passive_operator_evidence",
                "line": None,
                "ordinal": row.get("ordinal"),
                "blocking_reason": "passive_operator_evidence",
                "text": str(row.get("text") or ""),
                "artifact_id": str(artifact_status.get("artifact_id") or row.get("artifact_id") or ""),
                "artifact_status": str(
                    artifact_status.get("artifact_status")
                    or (artifact_payload if isinstance(artifact_payload, str) else "")
                ),
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


def _split_filter_values(value: str | list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    raw_values = [value] if isinstance(value, str) else list(value)
    out: list[str] = []
    for raw in raw_values:
        for part in str(raw or "").split(","):
            item = part.strip()
            if item and item not in out:
                out.append(item)
    return tuple(out)


def build_operator_next_actions(
    *,
    repo_root: str | Path | None = None,
    max_actions: int = 20,
    lane: str | None = None,
    reason: str | None = None,
    exclude_reasons: str | list[str] | tuple[str, ...] | None = None,
    action_source: str | None = None,
    backlog_lane: str | None = None,
    backlog_lane_ordinal: int | str | None = None,
    research_pipeline: str | None = None,
    research_artifact_lane: str | None = None,
    research_artifact_id: str | None = None,
    research_command_lane: str | None = None,
    research_command_input_class: str | None = None,
    research_command_id: str | None = None,
    operator_read_only_medium_lane_item: str | None = None,
    operator_read_only_command_id: str | None = None,
    operator_proof_category: str | None = None,
    operator_proof_line: int | str | None = None,
    operator_proof_passive_ordinal: int | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    limit = max(1, int(max_actions))
    lane_filter = str(lane or "").strip()
    reason_filter = str(reason or "").strip()
    exclude_reason_filters = _split_filter_values(exclude_reasons)
    source_filter = str(action_source or "").strip()
    backlog_lane_filter = str(backlog_lane or "").strip()
    backlog_lane_ordinal_filter = str(backlog_lane_ordinal or "").strip()
    research_pipeline_filter = str(research_pipeline or "").strip()
    research_artifact_lane_filter = str(research_artifact_lane or "").strip()
    research_artifact_id_filter = str(research_artifact_id or "").strip()
    research_command_lane_filter = str(research_command_lane or "").strip()
    research_command_input_filter = str(research_command_input_class or "").strip()
    research_command_id_filter = str(research_command_id or "").strip()
    operator_read_only_lane_item_filter = str(operator_read_only_medium_lane_item or "").strip()
    operator_read_only_command_filter = str(operator_read_only_command_id or "").strip()
    proof_category_filter = str(operator_proof_category or "").strip()
    proof_line_filter = str(operator_proof_line or "").strip()
    proof_passive_ordinal_filter = str(operator_proof_passive_ordinal or "").strip()
    invalid_lane_filter = bool(lane_filter) and lane_filter not in _ACTION_LANES
    source_action_lanes: set[str] = set()
    if backlog_lane_filter or backlog_lane_ordinal_filter:
        source_action_lanes.add("backlog_lane")
    if research_pipeline_filter:
        source_action_lanes.add("research_pipeline")
    if research_artifact_lane_filter or research_artifact_id_filter:
        source_action_lanes.add("research_artifact")
    if research_command_lane_filter or research_command_input_filter or research_command_id_filter:
        source_action_lanes.add("research_command")
    if operator_read_only_lane_item_filter or operator_read_only_command_filter:
        source_action_lanes.add("operator_read_only_command")
    if proof_category_filter or proof_line_filter:
        source_action_lanes.add("operator_proof")
    if proof_passive_ordinal_filter:
        source_action_lanes.add("passive_operator_evidence")
    bundle_kwargs: dict[str, Any] = {
        "repo_root": root,
        "backlog_lane": backlog_lane_filter or None,
        "backlog_lane_ordinal": backlog_lane_ordinal_filter or None,
        "research_pipeline": research_pipeline_filter or None,
        "research_artifact_lane": research_artifact_lane_filter or None,
        "research_artifact_id": research_artifact_id_filter or None,
        "research_command_lane": research_command_lane_filter or None,
        "research_command_input_class": research_command_input_filter or None,
        "research_command_id": research_command_id_filter or None,
        "operator_read_only_medium_lane_item": operator_read_only_lane_item_filter or None,
        "operator_read_only_command_id": operator_read_only_command_filter or None,
        "operator_proof_category": proof_category_filter or None,
        "operator_proof_line": proof_line_filter or None,
        "operator_proof_passive_ordinal": proof_passive_ordinal_filter or None,
    }
    if not lane_filter and len(source_action_lanes) == 1:
        bundle_kwargs["section"] = _SOURCE_ACTION_LANE_TO_SECTION[next(iter(source_action_lanes))]
    bundle = build_operator_status_bundle(**bundle_kwargs)
    summary = dict(bundle.get("summary") or {})
    planning_rows = _backlog_planning_rows(bundle)
    actions = [
        *_roadmap_actions(bundle),
        *_backlog_actions(bundle),
        *_research_actions(bundle),
        *_research_artifact_actions(bundle),
        *_research_command_actions(bundle),
        *_operator_read_only_command_actions(bundle),
        *_proof_actions(bundle),
        *_passive_operator_actions(bundle),
    ]
    if source_action_lanes and not lane_filter:
        actions = [row for row in actions if row.get("lane") in source_action_lanes]
    if invalid_lane_filter:
        actions = []
    elif lane_filter:
        actions = [row for row in actions if row.get("lane") == lane_filter]
    if reason_filter:
        actions = [row for row in actions if row.get("blocking_reason") == reason_filter]
    if exclude_reason_filters:
        actions = [row for row in actions if str(row.get("blocking_reason") or "") not in exclude_reason_filters]
    if source_filter:
        actions = [row for row in actions if row.get("source") == source_filter]
    required_total = (
        int(summary.get("roadmap_tracking_actions_required") or 0)
        + int(summary.get("research_pipeline_actions_required") or 0)
        + int(summary.get("research_artifact_actions_required") or 0)
        + int(summary.get("research_command_actions_required") or 0)
        + int(summary.get("operator_read_only_command_actions_required") or 0)
        + int(summary.get("passive_operator_evidence_actions_required") or 0)
        + int(summary.get("operator_proof_actions_required") or 0)
    )
    if lane_filter == "roadmap_tracking":
        required_total = int(summary.get("roadmap_tracking_actions_required") or 0)
    elif lane_filter == "backlog_lane":
        required_total = 0
    elif lane_filter == "research_pipeline":
        required_total = int(summary.get("research_pipeline_actions_required") or 0)
    elif lane_filter == "research_artifact":
        required_total = int(summary.get("research_artifact_actions_required") or 0)
    elif lane_filter == "research_command":
        required_total = int(summary.get("research_command_actions_required") or 0)
    elif lane_filter == "operator_read_only_command":
        required_total = int(summary.get("operator_read_only_command_actions_required") or 0)
    elif lane_filter == "operator_proof":
        required_total = int(summary.get("operator_proof_actions_required") or 0)
    elif lane_filter == "passive_operator_evidence":
        required_total = int(summary.get("passive_operator_evidence_actions_required") or 0)
    elif source_action_lanes:
        required_total = 0
        if "roadmap_tracking" in source_action_lanes:
            required_total += int(summary.get("roadmap_tracking_actions_required") or 0)
        if "research_pipeline" in source_action_lanes:
            required_total += int(summary.get("research_pipeline_actions_required") or 0)
        if "research_artifact" in source_action_lanes:
            required_total += int(summary.get("research_artifact_actions_required") or 0)
        if "research_command" in source_action_lanes:
            required_total += int(summary.get("research_command_actions_required") or 0)
        if "operator_read_only_command" in source_action_lanes:
            required_total += int(summary.get("operator_read_only_command_actions_required") or 0)
        if "operator_proof" in source_action_lanes:
            required_total += int(summary.get("operator_proof_actions_required") or 0)
    if reason_filter:
        # The source summary has lane totals, not reason totals; once filtered
        # by reason, the truthful total is the filtered available row count.
        required_total = len(actions)
    if exclude_reason_filters:
        # Exclusion filters are final action-row filters, not source-report
        # summary dimensions, so the truthful total is the remaining row count.
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
        "exclude_reason_filter": list(exclude_reason_filters),
        "action_source_filter": source_filter or None,
        "backlog_lane_filter": backlog_lane_filter or None,
        "backlog_lane_ordinal_filter": (
            int(backlog_lane_ordinal_filter) if backlog_lane_ordinal_filter.isdigit() else None
        ),
        "research_pipeline_filter": research_pipeline_filter or None,
        "research_artifact_lane_filter": research_artifact_lane_filter or None,
        "research_artifact_id_filter": research_artifact_id_filter or None,
        "research_command_lane_filter": research_command_lane_filter or None,
        "research_command_input_class_filter": research_command_input_filter or None,
        "research_command_id_filter": research_command_id_filter or None,
        "operator_read_only_medium_lane_item_filter": operator_read_only_lane_item_filter or None,
        "operator_read_only_command_id_filter": operator_read_only_command_filter or None,
        "operator_proof_category_filter": proof_category_filter or None,
        "operator_proof_line_filter": int(proof_line_filter) if proof_line_filter.isdigit() else None,
        "operator_proof_passive_ordinal_filter": (
            int(proof_passive_ordinal_filter) if proof_passive_ordinal_filter.isdigit() else None
        ),
        "source_reason": bundle.get("reason"),
        "source_reasons": dict(bundle.get("source_reasons") or {}),
        "source_report_type": bundle.get("report_type"),
        "source_summary": summary,
        "planning_row_count": len(planning_rows),
        "planning_rows": planning_rows,
        "summary": {
            "available_by_lane": _counts_by_key(actions, "lane"),
            "available_by_reason": _counts_by_key(actions, "blocking_reason"),
        },
        "action_count_total": required_total,
        "action_count_available": len(actions),
        "action_count_returned": min(len(actions), limit),
        "actions": actions[:limit],
    }
