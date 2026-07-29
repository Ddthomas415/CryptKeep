from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.backlog_lane_status import LANE_KEY_TO_HEADING, build_backlog_lane_status
from services.analytics.operator_proof_status import build_operator_proof_status
from services.analytics.research_command_status import build_research_command_status
from services.analytics.research_pipeline_status import build_research_pipeline_status


_SECTION_REPORT_KEYS = {
    "backlog": ("backlog_lane_status",),
    "research_pipeline": ("research_pipeline_status",),
    "research_command": ("research_command_status",),
    "operator_proof": ("operator_proof_status",),
}

_SECTION_ACTION_KEYS = {
    "backlog": ("backlog_lanes",),
    "research_pipeline": ("research_pipelines",),
    "research_command": ("research_commands",),
    "operator_proof": ("passive_operator_evidence", "operator_proofs"),
}


def _select_keys(payload: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: payload[key] for key in keys if key in payload}


def build_operator_status_bundle(
    *,
    repo_root: str | Path | None = None,
    section: str | None = None,
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
    section_filter = str(section or "").strip()
    available_sections = tuple(_SECTION_REPORT_KEYS)
    backlog_lane_filter = str(backlog_lane or "").strip()
    backlog_lane_ordinal_filter = str(backlog_lane_ordinal or "").strip()
    research_pipeline_filter = str(research_pipeline or "").strip()
    research_command_lane_filter = str(research_command_lane or "").strip()
    research_command_input_filter = str(research_command_input_class or "").strip()
    research_command_id_filter = str(research_command_id or "").strip()
    proof_category_filter = str(operator_proof_category or "").strip()
    proof_line_filter = str(operator_proof_line or "").strip()
    backlog = build_backlog_lane_status(repo_root=root, lane=backlog_lane_filter or None)
    research = build_research_pipeline_status(repo_root=root, pipeline=research_pipeline_filter or None)
    research_commands = build_research_command_status(
        repo_root=root,
        lane=research_command_lane_filter or None,
        input_class=research_command_input_filter or None,
        command_id=research_command_id_filter or None,
    )
    proofs = build_operator_proof_status(
        repo_root=root,
        category=proof_category_filter or None,
        line=proof_line_filter or None,
    )
    backlog_summary = dict(backlog.get("summary") or {})
    research_summary = dict(research.get("summary") or {})
    research_command_summary = dict(research_commands.get("summary") or {})
    proof_summary = dict(proofs.get("summary") or {})
    heading_to_key = {heading: key for key, heading in LANE_KEY_TO_HEADING.items()}
    source_backlog_actions = [
        {
            "lane_key": heading_to_key.get(str(lane_row.get("name") or ""), ""),
            "lane_name": str(lane_row.get("name") or ""),
            "ordinal": index,
            "text": str(item),
            "next_action": f"select or execute a scoped batch for {str(item)}",
        }
        for lane_row in list(backlog.get("lanes") or [])
        if isinstance(lane_row, dict)
        for index, item in enumerate(list(lane_row.get("items") or []), start=1)
        if backlog_lane_filter and str(item).strip()
    ]
    ordinal_value: int | None = None
    invalid_backlog_ordinal = False
    if backlog_lane_ordinal_filter:
        if not backlog_lane_filter or not backlog_lane_ordinal_filter.isdigit():
            invalid_backlog_ordinal = True
        else:
            ordinal_value = int(backlog_lane_ordinal_filter)
            invalid_backlog_ordinal = ordinal_value <= 0
    backlog_actions = list(source_backlog_actions)
    if ordinal_value is not None and not invalid_backlog_ordinal:
        backlog_actions = [row for row in backlog_actions if int(row.get("ordinal") or 0) == ordinal_value]
        if not backlog_actions:
            invalid_backlog_ordinal = True
    research_actions = [
        {
            "pipeline_id": str(row.get("pipeline_id") or ""),
            "latest_status": str(row.get("latest_status") or ""),
            "make_target": str(row.get("make_target") or ""),
            "blocking_reason": row.get("blocking_reason"),
            "next_action": str(row.get("next_action") or ""),
        }
        for row in list(research.get("pipelines") or [])
        if isinstance(row, dict) and bool(row.get("action_required"))
    ]
    research_command_actions = [
        {
            "command_id": str(row.get("command_id") or ""),
            "lane": str(row.get("lane") or ""),
            "input_class": str(row.get("input_class") or ""),
            "make_target": str(row.get("make_target") or ""),
            "blocking_reason": row.get("blocking_reason"),
            "next_action": str(row.get("next_action") or ""),
        }
        for row in list(research_commands.get("commands") or [])
        if isinstance(row, dict) and bool(row.get("action_required"))
    ]
    proof_actions = [
        {
            "line": row.get("line"),
            "category": str(row.get("category") or ""),
            "next_action": str(row.get("next_action") or ""),
        }
        for row in list(proofs.get("proof_markers") or [])
        if isinstance(row, dict) and bool(row.get("action_required"))
    ]
    passive_actions = [
        {
            "ordinal": row.get("ordinal"),
            "text": str(row.get("text") or ""),
            "next_action": str(row.get("next_action") or ""),
        }
        for row in list(proofs.get("passive_operator_items") or [])
        if isinstance(row, dict) and bool(row.get("action_required"))
    ]

    payload = {
        "schema_version": 1,
        "report_type": "operator_status_bundle",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": (
            bool(backlog.get("ok"))
            and bool(research.get("ok"))
            and bool(research_commands.get("ok"))
            and bool(proofs.get("ok"))
            and not invalid_backlog_ordinal
        ),
        "read_only": True,
        "planning_only": True,
        "does_not_close_proof": True,
        "does_not_run_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "repo_root": str(root),
        "backlog_lane_filter": backlog_lane_filter or None,
        "backlog_lane_ordinal_filter": ordinal_value,
        "research_pipeline_filter": research_pipeline_filter or None,
        "research_command_lane_filter": research_command_lane_filter or None,
        "research_command_input_class_filter": research_command_input_filter or None,
        "research_command_id_filter": research_command_id_filter or None,
        "operator_proof_category_filter": proof_category_filter or None,
        "operator_proof_line_filter": int(proof_line_filter) if proof_line_filter.isdigit() else None,
        "reports": {
            "backlog_lane_status": backlog,
            "research_pipeline_status": research,
            "research_command_status": research_commands,
            "operator_proof_status": proofs,
        },
        "actions": {
            "backlog_lanes": backlog_actions,
            "research_pipelines": research_actions,
            "research_commands": research_command_actions,
            "passive_operator_evidence": passive_actions,
            "operator_proofs": proof_actions[:10],
        },
        "summary": {
            "passive_operator_items": int(backlog_summary.get("passive_operator_evidence") or 0),
            "low_risk_docs_tests": int(backlog_summary.get("low_risk_docs_tests") or 0),
            "medium_risk_runtime_read_only": int(backlog_summary.get("medium_risk_runtime_read_only") or 0),
            "high_risk_gate_execution_deploy": int(backlog_summary.get("high_risk_gate_execution_deploy") or 0),
            "source_backlog_lane_actions_required": len(source_backlog_actions),
            "backlog_lane_actions_required": len(backlog_actions),
            "research_pipelines_wired": int(research_summary.get("wired") or 0),
            "research_pipelines_not_run": int(research_summary.get("not_run") or 0),
            "research_pipelines_latest_ok": int(research_summary.get("latest_ok") or 0),
            "research_pipeline_actions_required": len(research_actions),
            "research_commands_wired": int(research_command_summary.get("wired") or 0),
            "research_commands_not_wired": int(research_command_summary.get("not_wired") or 0),
            "research_command_actions_required": len(research_command_actions),
            "remaining_proof_or_coverage_markers": int(
                proof_summary.get("remaining_proof_or_coverage_markers") or 0
            ),
            "host_side_markers": int(proof_summary.get("host_side_markers") or 0),
            "proof_ready_markers": int(proof_summary.get("proof_ready_markers") or 0),
            "operator_proof_actions_required": len(proof_actions),
            "passive_operator_evidence_actions_required": len(passive_actions),
        },
    }
    if invalid_backlog_ordinal:
        payload["reason"] = "invalid_backlog_lane_ordinal"
    full_reports = dict(payload["reports"])
    full_actions = dict(payload["actions"])
    source_reasons = {
        key: value.get("reason")
        for key, value in full_reports.items()
        if isinstance(value, dict) and value.get("reason")
    }
    payload["source_reasons"] = source_reasons
    payload["available_sections"] = list(available_sections)
    payload["section_filter"] = section_filter or None
    payload["source_report_count"] = len(full_reports)
    payload["shown_report_count"] = len(full_reports)
    payload["source_action_count"] = sum(
        len(value) for value in full_actions.values() if isinstance(value, list)
    )
    payload["shown_action_count"] = payload["source_action_count"]

    if not section_filter:
        payload["shown_sections"] = list(available_sections)
        return payload

    if section_filter not in _SECTION_REPORT_KEYS:
        payload["ok"] = False
        payload["reason"] = "invalid_section"
        payload["shown_sections"] = []
        payload["reports"] = {}
        payload["actions"] = {}
        payload["shown_report_count"] = 0
        payload["shown_action_count"] = 0
        return payload

    payload["shown_sections"] = [section_filter]
    payload["reports"] = _select_keys(full_reports, _SECTION_REPORT_KEYS[section_filter])
    payload["actions"] = _select_keys(full_actions, _SECTION_ACTION_KEYS.get(section_filter, ()))
    payload["shown_report_count"] = len(payload["reports"])
    payload["shown_action_count"] = sum(
        len(value) for value in payload["actions"].values() if isinstance(value, list)
    )
    return payload
