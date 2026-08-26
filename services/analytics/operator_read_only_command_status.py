from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OperatorReadOnlyCommandSpec:
    command_id: str
    script: str
    make_target: str | None
    medium_lane_item: str
    input_class: str


OPERATOR_READ_ONLY_COMMANDS: tuple[OperatorReadOnlyCommandSpec, ...] = (
    OperatorReadOnlyCommandSpec(
        "managed_paper_campaign_planner",
        "scripts/plan_managed_paper_campaigns.py",
        None,
        "campaign_planner",
        "repo_artifacts",
    ),
    OperatorReadOnlyCommandSpec(
        "multi_symbol_paper_campaign_planner",
        "scripts/plan_multi_symbol_paper_campaigns.py",
        "plan-multi-symbol-paper-campaigns",
        "campaign_planner",
        "repo_artifacts",
    ),
    OperatorReadOnlyCommandSpec(
        "paper_campaign_status_formatter",
        "scripts/report_paper_campaign_status.py",
        None,
        "campaign_status_report",
        "status_payload",
    ),
    OperatorReadOnlyCommandSpec(
        "paper_gate_qualification",
        "scripts/report_paper_gate_qualification.py",
        "status-paper-gate-qualification",
        "gate_diagnostic",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "paper_gate_velocity",
        "scripts/report_paper_gate_velocity.py",
        "status-paper-gate-velocity",
        "gate_diagnostic",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "cost_assumptions",
        "scripts/check_cost_assumptions.py",
        "check-cost-assumptions",
        "gate_diagnostic",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "supervised_soak_status",
        "scripts/report_supervised_soak_status.py",
        "status-paper-soak",
        "campaign_status_report",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "hetzner_paper_campaign_status",
        "scripts/report_hetzner_paper_campaign_status.py",
        "status-paper-hetzner",
        "host_status_wrapper",
        "ssh_read_only",
    ),
    OperatorReadOnlyCommandSpec(
        "hetzner_crypto_edge_runtime_status",
        "scripts/report_hetzner_crypto_edge_runtime_status.py",
        "status-hetzner-edge-runtime",
        "host_status_wrapper",
        "ssh_read_only",
    ),
    OperatorReadOnlyCommandSpec(
        "hetzner_dependency_alignment_status",
        "scripts/report_hetzner_dependency_alignment_status.py",
        "status-hetzner-dependency-alignment",
        "host_status_wrapper",
        "ssh_read_only",
    ),
    OperatorReadOnlyCommandSpec(
        "hetzner_paper_host_health",
        "scripts/report_hetzner_paper_host_health.py",
        "check-hetzner-paper-host-health",
        "host_status_wrapper",
        "ssh_read_only",
    ),
    OperatorReadOnlyCommandSpec(
        "edge_cadence",
        "scripts/check_edge_cadence.py",
        "check-edge-cadence",
        "startup_host_diagnostic",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "dead_man",
        "scripts/check_dead_man.py",
        "check-dead-man",
        "startup_host_diagnostic",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "paper_campaign_ownership",
        "scripts/check_paper_campaign_ownership.py",
        "check-paper-campaign-ownership",
        "campaign_diagnostic",
        "manifest_input",
    ),
    OperatorReadOnlyCommandSpec(
        "system_diagnostics",
        "scripts/run_system_diagnostics.py",
        "system-diagnostics",
        "startup_host_diagnostic",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "ai_operator_oversight",
        "scripts/run_ai_operator_oversight.py",
        "ai-operator-oversight",
        "optional_operator_report",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "roadmap_tracking_status",
        "scripts/report_roadmap_tracking_status.py",
        "roadmap-tracking-status",
        "optional_operator_report",
        "repo_artifacts",
    ),
    OperatorReadOnlyCommandSpec(
        "supply_chain",
        "scripts/check_supply_chain.py",
        "check-supply-chain",
        "optional_operator_report",
        "repo_artifacts",
    ),
    OperatorReadOnlyCommandSpec(
        "operator_arm_to_halt_replay",
        "scripts/check_operator_arm_to_halt_replay.py",
        "operator-arm-to-halt-replay",
        "platform_event_packet",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "platform_event_journal",
        "scripts/report_platform_event_journal.py",
        "platform-event-journal",
        "platform_event_packet",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "platform_event_secrets",
        "scripts/check_platform_event_secrets.py",
        "platform-event-secrets",
        "platform_event_packet",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "platform_event_integrity",
        "scripts/check_platform_event_integrity.py",
        "platform-event-integrity",
        "platform_event_packet",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "platform_event_packet",
        "scripts/report_platform_event_packet.py",
        "platform-event-packet",
        "platform_event_packet",
        "local_state",
    ),
    OperatorReadOnlyCommandSpec(
        "live_intent_history_schema",
        "scripts/check_live_intent_history_schema.py",
        "live-intent-history-schema",
        "startup_host_diagnostic",
        "local_state",
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


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def _row(
    repo_root: Path,
    spec: OperatorReadOnlyCommandSpec,
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
        "medium_lane_item": spec.medium_lane_item,
        "input_class": spec.input_class,
        "script_exists": script_exists,
        "script_index_exists": script_index_exists,
        "make_target_exists": make_target_exists,
        "wiring_ok": wiring_ok,
        "reasons": reasons,
        "blocking_reason": reasons[0] if reasons else None,
        "next_action": (
            f"repair read-only command wiring for {spec.command_id}: "
            + ", ".join(reasons)
            if reasons
            else "none"
        ),
        "action_required": bool(reasons),
    }


def build_operator_read_only_command_status(
    *,
    repo_root: str | Path | None = None,
    medium_lane_item: str | None = None,
    command_id: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    lane_item_filter = str(medium_lane_item or "").strip()
    command_filter = str(command_id or "").strip()
    makefile_text = _read_text(root / "Makefile")
    scripts_text = _read_text(root / "scripts" / "SCRIPTS.md")
    all_rows = [
        _row(root, spec, makefile_text=makefile_text, scripts_text=scripts_text)
        for spec in OPERATOR_READ_ONLY_COMMANDS
    ]
    available_lane_items = sorted({str(row.get("medium_lane_item") or "") for row in all_rows})
    available_command_ids = [str(row.get("command_id") or "") for row in all_rows]
    invalid_lane_item = bool(lane_item_filter) and lane_item_filter not in available_lane_items
    invalid_command = bool(command_filter) and command_filter not in available_command_ids
    rows = all_rows
    if lane_item_filter:
        rows = [row for row in rows if row.get("medium_lane_item") == lane_item_filter]
    if command_filter:
        rows = [row for row in rows if row.get("command_id") == command_filter]
    wired = sum(1 for row in rows if bool(row.get("wiring_ok")))
    source_wired = sum(1 for row in all_rows if bool(row.get("wiring_ok")))
    reason = None
    if invalid_lane_item:
        reason = "invalid_medium_lane_item"
    elif invalid_command:
        reason = "invalid_command_id"
    return {
        "schema_version": 1,
        "report_type": "operator_read_only_command_status",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": reason is None and wired == len(rows),
        "read_only": True,
        "planning_only": True,
        "does_not_run_commands": True,
        "does_not_run_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_execution_input": True,
        "repo_root": str(root),
        "medium_lane_item_filter": lane_item_filter or None,
        "command_id_filter": command_filter or None,
        "available_medium_lane_items": available_lane_items,
        "available_command_ids": available_command_ids,
        "reason": reason,
        "makefile_sha256": _sha256(root / "Makefile"),
        "script_index_sha256": _sha256(root / "scripts" / "SCRIPTS.md"),
        "command_count": len(rows),
        "source_command_count": len(all_rows),
        "commands": [] if reason else rows,
        "summary": {
            "wired": 0 if reason else wired,
            "not_wired": 0 if reason else len(rows) - wired,
            "by_medium_lane_item": {} if reason else _count_by(rows, "medium_lane_item"),
            "by_input_class": {} if reason else _count_by(rows, "input_class"),
            "source_wired": source_wired,
            "source_not_wired": len(all_rows) - source_wired,
            "source_by_medium_lane_item": _count_by(all_rows, "medium_lane_item"),
            "source_by_input_class": _count_by(all_rows, "input_class"),
        },
    }
