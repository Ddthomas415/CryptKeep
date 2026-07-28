from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchCommandSpec:
    command_id: str
    script: str
    make_target: str | None
    lane: str
    input_class: str


RESEARCH_COMMANDS: tuple[ResearchCommandSpec, ...] = (
    ResearchCommandSpec(
        "ohlcv_archive_backfill",
        "scripts/research/run_ohlcv_archive_backfill.py",
        "ohlcv-archive-backfill",
        "archive",
        "operator_args",
    ),
    ResearchCommandSpec(
        "archive_walk_forward",
        "scripts/research/run_archive_walk_forward.py",
        "archive-walk-forward",
        "archive",
        "operator_args",
    ),
    ResearchCommandSpec(
        "archive_parameter_sweep",
        "scripts/research/run_archive_parameter_sweep.py",
        "archive-parameter-sweep",
        "archive",
        "operator_args",
    ),
    ResearchCommandSpec(
        "archive_parameter_sweep_triage",
        "scripts/research/run_archive_parameter_sweep_triage.py",
        "archive-parameter-sweep-triage",
        "archive",
        "artifact_input",
    ),
    ResearchCommandSpec(
        "funding_context_replay",
        "scripts/research/run_funding_context_replay.py",
        "funding-context-replay",
        "funding",
        "state_input",
    ),
    ResearchCommandSpec(
        "funding_context_price_join",
        "scripts/research/run_funding_context_price_join.py",
        "funding-context-price-join",
        "funding",
        "state_input",
    ),
    ResearchCommandSpec(
        "funding_threshold_sensitivity",
        "scripts/research/run_funding_threshold_sensitivity.py",
        "funding-threshold-sensitivity",
        "funding",
        "artifact_input",
    ),
    ResearchCommandSpec(
        "funding_threshold_window_stability",
        "scripts/research/run_funding_threshold_window_stability.py",
        "funding-threshold-window-stability",
        "funding",
        "artifact_input",
    ),
    ResearchCommandSpec(
        "funding_threshold_candidate_triage",
        "scripts/research/run_funding_threshold_candidate_triage.py",
        "funding-threshold-candidate-triage",
        "funding",
        "artifact_input",
    ),
    ResearchCommandSpec(
        "funding_threshold_stability_triage",
        "scripts/research/run_funding_threshold_stability_triage.py",
        "funding-threshold-stability-triage",
        "funding",
        "artifact_input",
    ),
    ResearchCommandSpec(
        "funding_threshold_pipeline",
        "scripts/research/run_funding_threshold_research_pipeline.py",
        "funding-threshold-research-pipeline",
        "funding",
        "state_input",
    ),
    ResearchCommandSpec(
        "crypto_edge_strategy_readiness",
        "scripts/research/run_crypto_edge_strategy_readiness.py",
        "crypto-edge-strategy-readiness",
        "funding",
        "state_input",
    ),
    ResearchCommandSpec(
        "price_action_context_labels",
        "scripts/research/run_price_action_context_labels.py",
        "price-action-context-labels",
        "price_action",
        "archive_input",
    ),
    ResearchCommandSpec(
        "price_action_forward_returns",
        "scripts/research/run_price_action_forward_returns.py",
        "price-action-forward-returns",
        "price_action",
        "artifact_input",
    ),
    ResearchCommandSpec(
        "price_action_window_stability",
        "scripts/research/run_price_action_window_stability.py",
        "price-action-window-stability",
        "price_action",
        "archive_input",
    ),
    ResearchCommandSpec(
        "price_action_candidate_triage",
        "scripts/research/run_price_action_candidate_triage.py",
        "price-action-candidate-triage",
        "price_action",
        "artifact_input",
    ),
    ResearchCommandSpec(
        "price_action_pipeline",
        "scripts/research/run_price_action_research_pipeline.py",
        "price-action-research-pipeline",
        "price_action",
        "archive_input",
    ),
    ResearchCommandSpec(
        "research_pipeline_status",
        "scripts/research/report_research_pipeline_status.py",
        "research-pipeline-status",
        "status",
        "none",
    ),
    ResearchCommandSpec(
        "research_command_status",
        "scripts/research/report_research_command_status.py",
        "research-command-status",
        "status",
        "none",
    ),
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _row(
    repo_root: Path,
    spec: ResearchCommandSpec,
    *,
    makefile_text: str,
    scripts_text: str,
) -> dict[str, Any]:
    script_path = repo_root / spec.script
    script_index_name = spec.script[len("scripts/") :] if spec.script.startswith("scripts/") else spec.script
    script_exists = script_path.is_file()
    script_index_exists = script_index_name in scripts_text or spec.script in scripts_text
    make_target_exists = True if spec.make_target is None else f"{spec.make_target}:" in makefile_text
    wiring_ok = bool(script_exists and script_index_exists and make_target_exists)
    reasons: list[str] = []
    if not script_exists:
        reasons.append("script_missing")
    if not script_index_exists:
        reasons.append("script_index_missing")
    if not make_target_exists:
        reasons.append("make_target_missing")
    return {
        "command_id": spec.command_id,
        "script": spec.script,
        "script_sha256": _sha256(script_path),
        "make_target": spec.make_target,
        "lane": spec.lane,
        "input_class": spec.input_class,
        "script_exists": script_exists,
        "script_index_exists": script_index_exists,
        "make_target_exists": make_target_exists,
        "wiring_ok": wiring_ok,
        "reasons": reasons,
    }


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        out[value] = out.get(value, 0) + 1
    return out


def build_research_command_status(*, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    makefile_text = _read_text(root / "Makefile")
    scripts_text = _read_text(root / "scripts" / "SCRIPTS.md")
    rows = [
        _row(root, spec, makefile_text=makefile_text, scripts_text=scripts_text)
        for spec in RESEARCH_COMMANDS
    ]
    wired = sum(1 for row in rows if bool(row.get("wiring_ok")))
    return {
        "schema_version": 1,
        "report_type": "research_command_status",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": wired == len(rows),
        "read_only": True,
        "not_research_execution": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_execution_input": True,
        "repo_root": str(root),
        "makefile_sha256": _sha256(root / "Makefile"),
        "script_index_sha256": _sha256(root / "scripts" / "SCRIPTS.md"),
        "command_count": len(rows),
        "commands": rows,
        "summary": {
            "wired": wired,
            "not_wired": len(rows) - wired,
            "by_lane": _count_by(rows, "lane"),
            "by_input_class": _count_by(rows, "input_class"),
        },
    }
