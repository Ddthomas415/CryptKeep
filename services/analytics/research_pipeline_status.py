from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchPipelineSpec:
    pipeline_id: str
    script: str
    make_target: str
    output_root: str
    expected_report_type: str
    expected_steps: tuple[str, ...]


PIPELINES: tuple[ResearchPipelineSpec, ...] = (
    ResearchPipelineSpec(
        pipeline_id="price_action",
        script="scripts/research/run_price_action_research_pipeline.py",
        make_target="price-action-research-pipeline",
        output_root=".cbp_state/data/research/price_action_pipeline",
        expected_report_type="price_action_research_pipeline",
        expected_steps=("context_labels", "forward_returns", "window_stability", "candidate_triage"),
    ),
    ResearchPipelineSpec(
        pipeline_id="funding_threshold",
        script="scripts/research/run_funding_threshold_research_pipeline.py",
        make_target="funding-threshold-research-pipeline",
        output_root=".cbp_state/data/research/funding_threshold_pipeline",
        expected_report_type="funding_threshold_research_pipeline",
        expected_steps=(
            "price_join",
            "threshold_sensitivity",
            "candidate_triage",
            "window_stability",
            "stability_triage",
        ),
    ),
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _latest_summary(output_root: Path) -> Path | None:
    if not output_root.exists():
        return None
    candidates = sorted(
        output_root.glob("*/pipeline_summary.json"),
        key=lambda item: item.stat().st_mtime if item.exists() else 0.0,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _step_names(payload: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(step.get("name") or "").strip()
        for step in list(payload.get("steps") or [])
        if isinstance(step, dict) and str(step.get("name") or "").strip()
    )


def _summary_status(
    *,
    spec: ResearchPipelineSpec,
    payload: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    if payload is None:
        return "not_run", ["latest_summary_missing"]
    reasons: list[str] = []
    if str(payload.get("report_type") or "") != spec.expected_report_type:
        reasons.append("unexpected_report_type")
    if not bool(payload.get("read_only")):
        reasons.append("missing_read_only_marker")
    missing_steps = [step for step in spec.expected_steps if step not in _step_names(payload)]
    if missing_steps:
        reasons.append("missing_expected_steps:" + ",".join(missing_steps))
    if bool(payload.get("ok")) and not reasons:
        return "latest_ok", []
    if not bool(payload.get("ok")):
        reasons.append("latest_summary_not_ok")
    return "latest_not_ok", reasons


def _pipeline_action(
    *,
    spec: ResearchPipelineSpec,
    status: str,
    reasons: list[str],
    wiring_ok: bool,
) -> tuple[str | None, str]:
    if not wiring_ok:
        return (
            "wiring_drift",
            f"repair script/Makefile/SCRIPTS registration for make {spec.make_target}",
        )
    if status == "not_run":
        return (
            "latest_summary_missing",
            f"run make {spec.make_target} with the required research inputs",
        )
    if status == "latest_not_ok":
        reason = reasons[0] if reasons else "latest_summary_not_ok"
        return (
            reason,
            f"inspect the latest {spec.pipeline_id} pipeline artifact, "
            f"fix the reported reason, then rerun make {spec.make_target}",
        )
    return None, "none"


def _pipeline_status(
    *,
    repo_root: Path,
    spec: ResearchPipelineSpec,
    makefile_text: str,
    scripts_text: str,
) -> dict[str, Any]:
    script_path = repo_root / spec.script
    output_root = repo_root / spec.output_root
    latest = _latest_summary(output_root)
    payload = _load_json(latest) if latest is not None else None
    status, reasons = _summary_status(spec=spec, payload=payload)
    script_exists = script_path.exists()
    make_target_exists = f"{spec.make_target}:" in makefile_text
    index_script = spec.script[len("scripts/") :] if spec.script.startswith("scripts/") else spec.script
    script_index_exists = index_script in scripts_text and f"make {spec.make_target}" in scripts_text
    wiring_ok = bool(script_exists and make_target_exists and script_index_exists)
    if not wiring_ok:
        if not script_exists:
            reasons.append("script_missing")
        if not make_target_exists:
            reasons.append("make_target_missing")
        if not script_index_exists:
            reasons.append("script_index_missing")

    blocking_reason, next_action = _pipeline_action(
        spec=spec,
        status=status,
        reasons=reasons,
        wiring_ok=wiring_ok,
    )

    return {
        "pipeline_id": spec.pipeline_id,
        "script": spec.script,
        "make_target": spec.make_target,
        "output_root": str(output_root),
        "wiring_ok": wiring_ok,
        "script_exists": script_exists,
        "make_target_exists": make_target_exists,
        "script_index_exists": script_index_exists,
        "latest_summary_path": str(latest) if latest is not None else None,
        "latest_summary_sha256": _sha256(latest) if latest is not None else None,
        "latest_status": status,
        "latest_ok": bool(payload.get("ok")) if payload is not None else None,
        "latest_generated_at": payload.get("generated_at") if payload is not None else None,
        "latest_step_count": len(_step_names(payload or {})),
        "expected_steps": list(spec.expected_steps),
        "reasons": reasons,
        "blocking_reason": blocking_reason,
        "next_action": next_action,
        "action_required": blocking_reason is not None,
    }


def build_research_pipeline_status(
    *,
    repo_root: str | Path | None = None,
    pipeline: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    pipeline_filter = str(pipeline or "").strip()
    makefile_text = _read_text(root / "Makefile")
    scripts_text = _read_text(root / "scripts" / "SCRIPTS.md")
    all_pipelines = [
        _pipeline_status(
            repo_root=root,
            spec=spec,
            makefile_text=makefile_text,
            scripts_text=scripts_text,
        )
        for spec in PIPELINES
    ]
    pipelines = all_pipelines
    if pipeline_filter:
        pipelines = [row for row in all_pipelines if row.get("pipeline_id") == pipeline_filter]
    wiring_ok = all(bool(item.get("wiring_ok")) for item in pipelines)
    return {
        "schema_version": 1,
        "report_type": "research_pipeline_status",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": wiring_ok,
        "read_only": True,
        "not_strategy_config": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_execution_input": True,
        "repo_root": str(root),
        "pipeline_filter": pipeline_filter or None,
        "pipeline_count": len(pipelines),
        "source_pipeline_count": len(all_pipelines),
        "pipelines": pipelines,
        "summary": {
            "wired": sum(1 for item in pipelines if bool(item.get("wiring_ok"))),
            "latest_ok": sum(1 for item in pipelines if item.get("latest_status") == "latest_ok"),
            "not_run": sum(1 for item in pipelines if item.get("latest_status") == "not_run"),
            "latest_not_ok": sum(1 for item in pipelines if item.get("latest_status") == "latest_not_ok"),
            "source_wired": sum(1 for item in all_pipelines if bool(item.get("wiring_ok"))),
            "source_latest_ok": sum(1 for item in all_pipelines if item.get("latest_status") == "latest_ok"),
        },
    }
