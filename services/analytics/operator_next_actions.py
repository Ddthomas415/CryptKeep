from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.operator_status_bundle import build_operator_status_bundle


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


def build_operator_next_actions(
    *,
    repo_root: str | Path | None = None,
    max_actions: int = 20,
    lane: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    limit = max(1, int(max_actions))
    lane_filter = str(lane or "").strip()
    bundle = build_operator_status_bundle(repo_root=root)
    summary = dict(bundle.get("summary") or {})
    actions = [*_research_actions(bundle), *_proof_actions(bundle)]
    if lane_filter:
        actions = [row for row in actions if row.get("lane") == lane_filter]
    required_total = int(summary.get("research_pipeline_actions_required") or 0) + int(
        summary.get("operator_proof_actions_required") or 0
    )
    if lane_filter == "research_pipeline":
        required_total = int(summary.get("research_pipeline_actions_required") or 0)
    elif lane_filter == "operator_proof":
        required_total = int(summary.get("operator_proof_actions_required") or 0)
    if required_total <= 0:
        required_total = len(actions)

    return {
        "schema_version": 1,
        "report_type": "operator_next_actions",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": bool(bundle.get("ok")),
        "read_only": True,
        "planning_only": True,
        "does_not_close_proof": True,
        "does_not_run_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "repo_root": str(root),
        "lane_filter": lane_filter or None,
        "source_report_type": bundle.get("report_type"),
        "source_summary": summary,
        "action_count_total": required_total,
        "action_count_available": len(actions),
        "action_count_returned": min(len(actions), limit),
        "actions": actions[:limit],
    }
