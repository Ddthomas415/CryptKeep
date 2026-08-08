from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROADMAP_DOC = "docs/ROADMAP_TRACKING_CHECKLIST.md"

REQUIRED_SOURCE_DOCS: tuple[str, ...] = (
    "REMAINING_TASKS.md",
    "docs/BACKLOG_EXECUTION_LANES.md",
    "docs/OPERATOR_GOVERNANCE_LANES.md",
    "docs/LAUNCH_CHECKLIST.md",
    "docs/research/strategy_expansion_roadmap.md",
    "docs/research/derivatives_intraday_roadmap.md",
    "docs/work_log/review_stabilized_work_log.md",
)

REQUIRED_COMMANDS: tuple[str, ...] = (
    "make roadmap-tracking-status-json",
    "make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20",
    "make operator-proof-status-json",
    "make operator-read-only-command-status-json",
    "make backlog-lane-status-json",
    "make status-paper-gate-velocity-json",
    "make status-paper-campaigns",
    "make check-cost-assumptions-json",
    "make check-edge-cadence-json",
    "make research-pipeline-status-json",
    "make research-command-status-json",
)

REQUIRED_BOUNDARY_PHRASES: tuple[str, ...] = (
    "It does not replace `REMAINING_TASKS.md`",
    "This checklist does not authorize:",
    "live trading;",
    "Current operating phase: paper-evidence collection and read-only research.",
    "deterministic trading/risk engine remains the only authority",
    "Batch only items from the same lane.",
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _make_target(command: str) -> str | None:
    parts = command.split()
    if len(parts) < 2 or parts[0] != "make":
        return None
    return parts[1]


def build_roadmap_tracking_status(*, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    roadmap_path = root / ROADMAP_DOC
    roadmap_text = _read_text(roadmap_path)
    makefile_text = _read_text(root / "Makefile")
    backlog_text = _read_text(root / "REMAINING_TASKS.md")
    lane_map_text = _read_text(root / "docs" / "BACKLOG_EXECUTION_LANES.md")

    source_docs = []
    for rel in REQUIRED_SOURCE_DOCS:
        path = root / rel
        source_docs.append(
            {
                "path": rel,
                "exists": path.is_file(),
                "sha256": _sha256(path),
                "linked_from_roadmap": rel in roadmap_text,
            }
        )

    command_rows = []
    for command in REQUIRED_COMMANDS:
        target = _make_target(command)
        makefile_has_target = bool(target and f"{target}:" in makefile_text)
        command_rows.append(
            {
                "command": command,
                "make_target": target,
                "listed_in_roadmap": command in roadmap_text,
                "makefile_has_target": makefile_has_target,
            }
        )

    boundary_rows = [
        {"phrase": phrase, "present": phrase in roadmap_text}
        for phrase in REQUIRED_BOUNDARY_PHRASES
    ]
    linked_from_backlog = ROADMAP_DOC in backlog_text
    linked_from_lane_map = ROADMAP_DOC in lane_map_text
    missing_docs = [row["path"] for row in source_docs if not row["exists"]]
    unlinked_docs = [row["path"] for row in source_docs if not row["linked_from_roadmap"]]
    missing_commands = [row["command"] for row in command_rows if not row["listed_in_roadmap"]]
    missing_make_targets = [
        row["make_target"]
        for row in command_rows
        if row["make_target"] and not row["makefile_has_target"]
    ]
    missing_boundaries = [row["phrase"] for row in boundary_rows if not row["present"]]
    ok = bool(
        roadmap_text
        and not missing_docs
        and not unlinked_docs
        and not missing_commands
        and not missing_make_targets
        and not missing_boundaries
        and linked_from_backlog
        and linked_from_lane_map
    )
    reason = None
    if not ok:
        reason = "roadmap_tracking_incomplete"

    return {
        "schema_version": 1,
        "report_type": "roadmap_tracking_status",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "reason": reason,
        "read_only": True,
        "planning_only": True,
        "does_not_decide_backlog_items": True,
        "does_not_close_proof": True,
        "does_not_run_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "repo_root": str(root),
        "roadmap_doc": str(roadmap_path),
        "roadmap_doc_sha256": _sha256(roadmap_path),
        "linked_from_backlog": linked_from_backlog,
        "linked_from_lane_map": linked_from_lane_map,
        "source_docs": source_docs,
        "commands": command_rows,
        "boundaries": boundary_rows,
        "missing_docs": missing_docs,
        "unlinked_docs": unlinked_docs,
        "missing_commands": missing_commands,
        "missing_make_targets": missing_make_targets,
        "missing_boundaries": missing_boundaries,
        "summary": {
            "source_doc_count": len(source_docs),
            "source_docs_present": len(source_docs) - len(missing_docs),
            "source_docs_linked": len(source_docs) - len(unlinked_docs),
            "command_count": len(command_rows),
            "commands_listed": len(command_rows) - len(missing_commands),
            "make_targets_present": len(command_rows) - len(missing_make_targets),
            "boundary_count": len(boundary_rows),
            "boundaries_present": len(boundary_rows) - len(missing_boundaries),
        },
    }
