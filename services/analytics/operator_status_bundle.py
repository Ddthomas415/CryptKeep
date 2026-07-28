from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.backlog_lane_status import build_backlog_lane_status
from services.analytics.operator_proof_status import build_operator_proof_status
from services.analytics.research_pipeline_status import build_research_pipeline_status


def build_operator_status_bundle(*, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    backlog = build_backlog_lane_status(repo_root=root)
    research = build_research_pipeline_status(repo_root=root)
    proofs = build_operator_proof_status(repo_root=root)
    backlog_summary = dict(backlog.get("summary") or {})
    research_summary = dict(research.get("summary") or {})
    proof_summary = dict(proofs.get("summary") or {})

    return {
        "schema_version": 1,
        "report_type": "operator_status_bundle",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": bool(backlog.get("ok")) and bool(research.get("ok")) and bool(proofs.get("ok")),
        "read_only": True,
        "planning_only": True,
        "does_not_close_proof": True,
        "does_not_run_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "repo_root": str(root),
        "reports": {
            "backlog_lane_status": backlog,
            "research_pipeline_status": research,
            "operator_proof_status": proofs,
        },
        "summary": {
            "passive_operator_items": int(backlog_summary.get("passive_operator_evidence") or 0),
            "low_risk_docs_tests": int(backlog_summary.get("low_risk_docs_tests") or 0),
            "medium_risk_runtime_read_only": int(backlog_summary.get("medium_risk_runtime_read_only") or 0),
            "high_risk_gate_execution_deploy": int(backlog_summary.get("high_risk_gate_execution_deploy") or 0),
            "research_pipelines_wired": int(research_summary.get("wired") or 0),
            "research_pipelines_not_run": int(research_summary.get("not_run") or 0),
            "research_pipelines_latest_ok": int(research_summary.get("latest_ok") or 0),
            "remaining_proof_or_coverage_markers": int(
                proof_summary.get("remaining_proof_or_coverage_markers") or 0
            ),
            "host_side_markers": int(proof_summary.get("host_side_markers") or 0),
            "proof_ready_markers": int(proof_summary.get("proof_ready_markers") or 0),
        },
    }
