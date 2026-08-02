from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BOUNDARY_KEYS: tuple[str, ...] = (
    "read_only",
    "not_strategy_config",
    "not_campaign_evidence",
    "not_promotion_evidence",
    "not_execution_input",
    "not_profitability_evidence",
)

RESEARCH_ARTIFACT_BOUNDARY_DEFAULTS: dict[str, bool] = {
    "read_only": True,
    "not_strategy_config": True,
    "not_campaign_evidence": True,
    "not_promotion_evidence": True,
    "not_execution_input": True,
}


@dataclass(frozen=True)
class ResearchArtifactSpec:
    artifact_id: str
    lane: str
    artifact_class: str
    glob_pattern: str
    marker_key: str
    marker_value: str
    producer_make_target: str
    producer_args_variable: str | None = None
    required_inputs: tuple[str, ...] = ()


ARTIFACTS: tuple[ResearchArtifactSpec, ...] = (
    ResearchArtifactSpec(
        "archive_walk_forward",
        "archive",
        "walk_forward",
        ".cbp_state/data/research/archive_walk_forward/**/*.json",
        "artifact_type",
        "archive_backed_walk_forward_v1",
        "archive-walk-forward",
        "ARCHIVE_WALK_FORWARD_ARGS",
        ("strategy config", "venue/symbol/timeframe", "archive row window", "output path"),
    ),
    ResearchArtifactSpec(
        "archive_parameter_sweep",
        "archive",
        "parameter_sweep",
        ".cbp_state/data/research/archive_parameter_sweep/**/*.json",
        "artifact_type",
        "archive_backed_parameter_sweep_v1",
        "archive-parameter-sweep",
        "ARCHIVE_PARAMETER_SWEEP_ARGS",
        ("base strategy config", "parameter grid", "venue/symbol/timeframe", "archive row window", "output path"),
    ),
    ResearchArtifactSpec(
        "archive_parameter_sweep_triage",
        "archive",
        "parameter_sweep",
        ".cbp_state/data/research/archive_parameter_sweep_triage/**/*.json",
        "artifact_type",
        "archive_parameter_sweep_triage_v1",
        "archive-parameter-sweep-triage",
        "ARCHIVE_PARAMETER_SWEEP_TRIAGE_ARGS",
        ("input archive_parameter_sweep artifact", "output path"),
    ),
    ResearchArtifactSpec(
        "funding_threshold_pipeline_summary",
        "funding",
        "pipeline_summary",
        ".cbp_state/data/research/funding_threshold_pipeline/*/pipeline_summary.json",
        "report_type",
        "funding_threshold_research_pipeline",
        "funding-threshold-research-pipeline",
        "FUNDING_THRESHOLD_RESEARCH_PIPELINE_ARGS",
        ("accepted funding/context input state", "output path"),
    ),
    ResearchArtifactSpec(
        "funding_context_price_join",
        "funding",
        "funding_context",
        ".cbp_state/data/research/funding_threshold_pipeline/*/funding_context_price_join.json",
        "artifact_type",
        "funding_context_price_join_v1",
        "funding-threshold-research-pipeline",
        "FUNDING_THRESHOLD_RESEARCH_PIPELINE_ARGS",
        ("accepted funding/context input state", "output path"),
    ),
    ResearchArtifactSpec(
        "funding_threshold_sensitivity",
        "funding",
        "funding_threshold",
        ".cbp_state/data/research/funding_threshold_pipeline/*/funding_threshold_sensitivity.json",
        "artifact_type",
        "funding_threshold_sensitivity_v1",
        "funding-threshold-research-pipeline",
        "FUNDING_THRESHOLD_RESEARCH_PIPELINE_ARGS",
        ("accepted funding/context input state", "output path"),
    ),
    ResearchArtifactSpec(
        "funding_threshold_window_stability",
        "funding",
        "funding_threshold",
        ".cbp_state/data/research/funding_threshold_pipeline/*/funding_threshold_window_stability.json",
        "artifact_type",
        "funding_threshold_window_stability_v1",
        "funding-threshold-research-pipeline",
        "FUNDING_THRESHOLD_RESEARCH_PIPELINE_ARGS",
        ("accepted funding/context input state", "output path"),
    ),
    ResearchArtifactSpec(
        "funding_threshold_candidate_triage",
        "funding",
        "funding_threshold",
        ".cbp_state/data/research/funding_threshold_pipeline/*/funding_threshold_candidate_triage.json",
        "artifact_type",
        "funding_threshold_candidate_triage_v1",
        "funding-threshold-research-pipeline",
        "FUNDING_THRESHOLD_RESEARCH_PIPELINE_ARGS",
        ("accepted funding/context input state", "output path"),
    ),
    ResearchArtifactSpec(
        "funding_threshold_stability_triage",
        "funding",
        "funding_threshold",
        ".cbp_state/data/research/funding_threshold_pipeline/*/funding_threshold_stability_triage.json",
        "artifact_type",
        "funding_threshold_stability_triage_v1",
        "funding-threshold-research-pipeline",
        "FUNDING_THRESHOLD_RESEARCH_PIPELINE_ARGS",
        ("accepted funding/context input state", "output path"),
    ),
    ResearchArtifactSpec(
        "price_action_pipeline_summary",
        "price_action",
        "pipeline_summary",
        ".cbp_state/data/research/price_action_pipeline/*/pipeline_summary.json",
        "report_type",
        "price_action_research_pipeline",
        "price-action-research-pipeline",
        "PRICE_ACTION_RESEARCH_PIPELINE_ARGS",
        ("accepted OHLCV archive input", "output path"),
    ),
    ResearchArtifactSpec(
        "price_action_context_labels",
        "price_action",
        "price_action",
        ".cbp_state/data/research/price_action_pipeline/*/context_labels.json",
        "artifact_type",
        "price_action_context_labels_v1",
        "price-action-research-pipeline",
        "PRICE_ACTION_RESEARCH_PIPELINE_ARGS",
        ("accepted OHLCV archive input", "output path"),
    ),
    ResearchArtifactSpec(
        "price_action_forward_returns",
        "price_action",
        "price_action",
        ".cbp_state/data/research/price_action_pipeline/*/forward_returns.json",
        "artifact_type",
        "price_action_forward_returns_v1",
        "price-action-research-pipeline",
        "PRICE_ACTION_RESEARCH_PIPELINE_ARGS",
        ("accepted OHLCV archive input", "output path"),
    ),
    ResearchArtifactSpec(
        "price_action_window_stability",
        "price_action",
        "price_action",
        ".cbp_state/data/research/price_action_pipeline/*/window_stability.json",
        "artifact_type",
        "price_action_window_stability_v1",
        "price-action-research-pipeline",
        "PRICE_ACTION_RESEARCH_PIPELINE_ARGS",
        ("accepted OHLCV archive input", "output path"),
    ),
    ResearchArtifactSpec(
        "price_action_candidate_triage",
        "price_action",
        "price_action",
        ".cbp_state/data/research/price_action_pipeline/*/candidate_triage.json",
        "artifact_type",
        "price_action_candidate_triage_v1",
        "price-action-research-pipeline",
        "PRICE_ACTION_RESEARCH_PIPELINE_ARGS",
        ("accepted OHLCV archive input", "output path"),
    ),
)


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return sorted(
        paths,
        key=lambda item: (item.stat().st_mtime if item.exists() else 0.0, str(item)),
        reverse=True,
    )[0]


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        out[value] = out.get(value, 0) + 1
    return out


def _generated_at(payload: dict[str, Any]) -> str | None:
    for key in ("generated_at", "created_at", "timestamp"):
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def _boundary_flags(payload: dict[str, Any] | None) -> dict[str, bool | None]:
    payload = payload or {}
    return {
        key: (
            bool(payload[key])
            if key in payload
            else RESEARCH_ARTIFACT_BOUNDARY_DEFAULTS.get(key)
            if key in RESEARCH_ARTIFACT_BOUNDARY_DEFAULTS
            else None
        )
        for key in BOUNDARY_KEYS
    }


def _boundary_flag_sources(payload: dict[str, Any] | None) -> dict[str, str]:
    payload = payload or {}
    return {
        key: (
            "payload"
            if key in payload
            else "registry_default"
            if key in RESEARCH_ARTIFACT_BOUNDARY_DEFAULTS
            else "absent"
        )
        for key in BOUNDARY_KEYS
    }


def _terminal_research_result(spec: ResearchArtifactSpec, payload: dict[str, Any]) -> str | None:
    """Classify completed negative research findings that should not be rerun.

    Some research artifacts use ok=false to mean "the triage found no accepted
    candidate", not "the artifact failed to run." Keep this narrow so malformed
    or unsupported artifacts still fail closed.
    """
    if (
        spec.artifact_id == "archive_parameter_sweep_triage"
        and str(payload.get("reason") or "") == "insufficient_review_candidates"
        and isinstance(payload.get("candidates"), list)
        and isinstance(payload.get("review_candidates"), list)
    ):
        return "latest_terminal_no_candidates"
    return None


def _producer_plan(spec: ResearchArtifactSpec) -> dict[str, Any]:
    required_inputs = list(spec.required_inputs)
    args_variable = str(spec.producer_args_variable or "")
    command_hint = f"make {spec.producer_make_target}"
    if args_variable:
        command_hint += f' {args_variable}="<accepted inputs>"'
    return {
        "make_target": spec.producer_make_target,
        "make_args_variable": args_variable or None,
        "required_inputs": required_inputs,
        "requires_accepted_inputs": bool(required_inputs),
        "command_hint": command_hint,
    }


def _missing_next_action(spec: ResearchArtifactSpec) -> str:
    plan = _producer_plan(spec)
    if plan["requires_accepted_inputs"]:
        inputs = ", ".join(str(item) for item in plan["required_inputs"])
        return f"select accepted inputs ({inputs}), then run {plan['command_hint']}"
    return f"run make {spec.producer_make_target}"


def _row(repo_root: Path, spec: ResearchArtifactSpec) -> dict[str, Any]:
    paths = [path for path in repo_root.glob(spec.glob_pattern) if path.is_file()]
    latest = _latest(paths)
    if latest is None:
        return {
            "artifact_id": spec.artifact_id,
            "lane": spec.lane,
            "artifact_class": spec.artifact_class,
            "glob_pattern": spec.glob_pattern,
            "producer_make_target": spec.producer_make_target,
            "latest_status": "missing",
            "latest_path": None,
            "latest_sha256": None,
            "latest_ok": None,
            "latest_generated_at": None,
            "artifact_count": 0,
            "marker_key": spec.marker_key,
            "expected_marker": spec.marker_value,
            "observed_marker": None,
            "producer_plan": _producer_plan(spec),
            "boundary_flags": _boundary_flags(None),
            "boundary_flag_sources": _boundary_flag_sources(None),
            "blocking_reason": "latest_artifact_missing",
            "next_action": _missing_next_action(spec),
            "action_required": True,
        }

    payload = _load_json(latest)
    if payload is None:
        return {
            "artifact_id": spec.artifact_id,
            "lane": spec.lane,
            "artifact_class": spec.artifact_class,
            "glob_pattern": spec.glob_pattern,
            "producer_make_target": spec.producer_make_target,
            "latest_status": "unreadable",
            "latest_path": str(latest),
            "latest_sha256": _sha256(latest),
            "latest_ok": None,
            "latest_generated_at": None,
            "artifact_count": len(paths),
            "marker_key": spec.marker_key,
            "expected_marker": spec.marker_value,
            "observed_marker": None,
            "producer_plan": _producer_plan(spec),
            "boundary_flags": _boundary_flags(None),
            "boundary_flag_sources": _boundary_flag_sources(None),
            "blocking_reason": "latest_artifact_unreadable",
            "next_action": f"inspect or regenerate {latest}",
            "action_required": True,
        }

    marker = str(payload.get(spec.marker_key) or "")
    reasons: list[str] = []
    if marker != spec.marker_value:
        reasons.append("unexpected_artifact_marker")
    terminal_status = _terminal_research_result(spec, payload) if not reasons else None
    if payload.get("ok") is False and terminal_status is None:
        reasons.append("latest_artifact_not_ok")
    status = terminal_status or ("latest_ok" if not reasons else "latest_not_ok")
    blocking_reason = reasons[0] if reasons else None
    next_action = (
        f"inspect latest {spec.artifact_id} artifact, then rerun make {spec.producer_make_target}"
        if blocking_reason
        else "none"
    )
    return {
        "artifact_id": spec.artifact_id,
        "lane": spec.lane,
        "artifact_class": spec.artifact_class,
        "glob_pattern": spec.glob_pattern,
        "producer_make_target": spec.producer_make_target,
        "latest_status": status,
        "latest_path": str(latest),
        "latest_sha256": _sha256(latest),
        "latest_ok": bool(payload.get("ok")) if "ok" in payload else None,
        "latest_generated_at": _generated_at(payload),
        "artifact_count": len(paths),
        "marker_key": spec.marker_key,
        "expected_marker": spec.marker_value,
        "observed_marker": marker,
        "producer_plan": _producer_plan(spec),
        "boundary_flags": _boundary_flags(payload),
        "boundary_flag_sources": _boundary_flag_sources(payload),
        "blocking_reason": blocking_reason,
        "next_action": next_action,
        "action_required": blocking_reason is not None,
    }


def build_research_artifact_inventory(
    *,
    repo_root: str | Path | None = None,
    lane: str | None = None,
    artifact_id: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    lane_filter = str(lane or "").strip()
    artifact_filter = str(artifact_id or "").strip()
    all_rows = [_row(root, spec) for spec in ARTIFACTS]
    available_artifact_ids = [str(row.get("artifact_id") or "") for row in all_rows]
    available_lanes = sorted({str(row.get("lane") or "") for row in all_rows if str(row.get("lane") or "")})
    valid_artifact_filter = not artifact_filter or artifact_filter in available_artifact_ids
    valid_lane_filter = not lane_filter or lane_filter in available_lanes
    rows = all_rows
    if lane_filter:
        rows = [row for row in rows if row.get("lane") == lane_filter]
    if artifact_filter:
        rows = [row for row in rows if row.get("artifact_id") == artifact_filter]
    hard_failures = {
        "unreadable",
        "latest_not_ok",
    }
    return {
        "schema_version": 1,
        "report_type": "research_artifact_inventory",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": bool(
            valid_lane_filter
            and valid_artifact_filter
            and not any(row.get("latest_status") in hard_failures for row in rows)
        ),
        "reason": (
            "invalid_lane"
            if not valid_lane_filter
            else "invalid_artifact_id"
            if not valid_artifact_filter
            else None
        ),
        "read_only": True,
        "does_not_run_research": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "not_strategy_config": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_execution_input": True,
        "repo_root": str(root),
        "lane_filter": lane_filter or None,
        "artifact_id_filter": artifact_filter or None,
        "available_lanes": available_lanes,
        "available_artifact_ids": available_artifact_ids,
        "artifact_count": len(rows),
        "source_artifact_count": len(all_rows),
        "artifacts": rows,
        "summary": {
            "found": sum(1 for row in rows if row.get("latest_path")),
            "missing": sum(1 for row in rows if row.get("latest_status") == "missing"),
            "latest_ok": sum(1 for row in rows if row.get("latest_status") == "latest_ok"),
            "terminal_no_candidates": sum(
                1 for row in rows if row.get("latest_status") == "latest_terminal_no_candidates"
            ),
            "latest_not_ok": sum(1 for row in rows if row.get("latest_status") == "latest_not_ok"),
            "unreadable": sum(1 for row in rows if row.get("latest_status") == "unreadable"),
            "action_required": sum(1 for row in rows if bool(row.get("action_required"))),
            "by_lane": _count_by(rows, "lane"),
            "source_by_lane": _count_by(all_rows, "lane"),
        },
    }
