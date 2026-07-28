from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.backlog_lane_status import build_backlog_lane_status
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
    "research_pipeline": ("research_pipelines",),
    "operator_proof": ("operator_proofs",),
}


def _select_keys(payload: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: payload[key] for key in keys if key in payload}


def build_operator_status_bundle(
    *,
    repo_root: str | Path | None = None,
    section: str | None = None,
    backlog_lane: str | None = None,
    research_command_lane: str | None = None,
    research_command_input_class: str | None = None,
    operator_proof_category: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    section_filter = str(section or "").strip()
    available_sections = tuple(_SECTION_REPORT_KEYS)
    backlog_lane_filter = str(backlog_lane or "").strip()
    research_command_lane_filter = str(research_command_lane or "").strip()
    research_command_input_filter = str(research_command_input_class or "").strip()
    proof_category_filter = str(operator_proof_category or "").strip()
    backlog = build_backlog_lane_status(repo_root=root, lane=backlog_lane_filter or None)
    research = build_research_pipeline_status(repo_root=root)
    research_commands = build_research_command_status(
        repo_root=root,
        lane=research_command_lane_filter or None,
        input_class=research_command_input_filter or None,
    )
    proofs = build_operator_proof_status(repo_root=root, category=proof_category_filter or None)
    backlog_summary = dict(backlog.get("summary") or {})
    research_summary = dict(research.get("summary") or {})
    research_command_summary = dict(research_commands.get("summary") or {})
    proof_summary = dict(proofs.get("summary") or {})
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
    proof_actions = [
        {
            "line": row.get("line"),
            "category": str(row.get("category") or ""),
            "next_action": str(row.get("next_action") or ""),
        }
        for row in list(proofs.get("proof_markers") or [])
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
        ),
        "read_only": True,
        "planning_only": True,
        "does_not_close_proof": True,
        "does_not_run_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "repo_root": str(root),
        "backlog_lane_filter": backlog_lane_filter or None,
        "research_command_lane_filter": research_command_lane_filter or None,
        "research_command_input_class_filter": research_command_input_filter or None,
        "operator_proof_category_filter": proof_category_filter or None,
        "reports": {
            "backlog_lane_status": backlog,
            "research_pipeline_status": research,
            "research_command_status": research_commands,
            "operator_proof_status": proofs,
        },
        "actions": {
            "research_pipelines": research_actions,
            "operator_proofs": proof_actions[:10],
        },
        "summary": {
            "passive_operator_items": int(backlog_summary.get("passive_operator_evidence") or 0),
            "low_risk_docs_tests": int(backlog_summary.get("low_risk_docs_tests") or 0),
            "medium_risk_runtime_read_only": int(backlog_summary.get("medium_risk_runtime_read_only") or 0),
            "high_risk_gate_execution_deploy": int(backlog_summary.get("high_risk_gate_execution_deploy") or 0),
            "research_pipelines_wired": int(research_summary.get("wired") or 0),
            "research_pipelines_not_run": int(research_summary.get("not_run") or 0),
            "research_pipelines_latest_ok": int(research_summary.get("latest_ok") or 0),
            "research_pipeline_actions_required": len(research_actions),
            "research_commands_wired": int(research_command_summary.get("wired") or 0),
            "research_commands_not_wired": int(research_command_summary.get("not_wired") or 0),
            "remaining_proof_or_coverage_markers": int(
                proof_summary.get("remaining_proof_or_coverage_markers") or 0
            ),
            "host_side_markers": int(proof_summary.get("host_side_markers") or 0),
            "proof_ready_markers": int(proof_summary.get("proof_ready_markers") or 0),
            "operator_proof_actions_required": len(proof_actions),
        },
    }
    full_reports = dict(payload["reports"])
    full_actions = dict(payload["actions"])
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
