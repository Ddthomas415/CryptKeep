from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PASSIVE_HEADING = "Passive / Operator Evidence"

_MARKERS: tuple[tuple[str, str], ...] = (
    ("remaining_capped_live_proof", "remaining capped-live proof"),
    ("remaining_operational_proof", "remaining operational proof"),
    ("remaining_proof", "remaining proof"),
    ("remaining_coverage", "remaining coverage"),
    ("proof_ready_implementation", "proof-ready"),
    ("host_side_reference", "operator-host"),
    ("host_side_reference", "host proof"),
    ("host_side_reference", "host-side"),
)


@dataclass(frozen=True)
class ProofMarker:
    line: int
    category: str
    marker: str
    text: str
    context: str = ""


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


def _section(text: str, heading: str) -> str:
    marker = f"### {heading}"
    if marker not in text:
        return ""
    tail = text.split(marker, 1)[1]
    if "\n### " in tail:
        return tail.split("\n### ", 1)[0]
    if "\n## " in tail:
        return tail.split("\n## ", 1)[0]
    return tail


def _bullet_items(section: str) -> tuple[str, ...]:
    items: list[str] = []
    current: list[str] = []
    for raw in section.splitlines():
        line = raw.rstrip()
        if line.startswith("- "):
            if current:
                items.append(" ".join(part.strip() for part in current).strip())
            current = [line[2:].strip()]
            continue
        if current and line.startswith("  ") and line.strip():
            current.append(line.strip())
            continue
        if current and not line.strip():
            items.append(" ".join(part.strip() for part in current).strip())
            current = []
    if current:
        items.append(" ".join(part.strip() for part in current).strip())
    return tuple(item for item in items if item)


def _proof_markers(backlog_text: str) -> tuple[ProofMarker, ...]:
    markers: list[ProofMarker] = []
    lines = backlog_text.splitlines()
    for line_no, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text:
            continue
        context = _numbered_item_context(lines, line_no)
        lowered = text.lower()
        for category, marker in _MARKERS:
            if marker in lowered:
                category = _effective_marker_category(category, text=text, context=context)
                markers.append(
                    ProofMarker(
                        line=line_no,
                        category=category,
                        marker=marker,
                        text=text,
                        context=context,
                    )
                )
                break
    return tuple(markers)


def _numbered_item_context(lines: list[str], line_no: int) -> str:
    start = line_no - 1
    while start > 0 and not re.match(r"^\s*\d+\.\s+", lines[start]):
        start -= 1
    end = line_no
    while end < len(lines) and not re.match(r"^\s*\d+\.\s+", lines[end]):
        end += 1
    return " ".join(part.strip() for part in lines[start:end] if part.strip())


def _effective_marker_category(category: str, *, text: str, context: str) -> str:
    if category != "remaining_proof":
        return category
    combined = f"{text} {context}".lower()
    if "crypto-edge" in combined:
        return category
    marker_text = text.lower()
    host_line_phrases = (
        "host-side",
        "operator-host",
        "host proof",
        "host-specific",
        "hetzner",
        "/srv/cryptkeep",
        "/var/lib/cbp",
    )
    host_context_phrases = (
        "host-side restore drill",
        "host-side promotion proof",
        "host-specific storage proof",
        "hetzner canonical",
        "future launch-packet host evidence",
    )
    if any(phrase in marker_text for phrase in host_line_phrases) or any(
        phrase in combined for phrase in host_context_phrases
    ):
        return "host_side_reference"
    return category


def _category_counts(markers: tuple[ProofMarker, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for marker in markers:
        out[marker.category] = out.get(marker.category, 0) + 1
    return out


def _marker_next_action(marker: ProofMarker) -> str:
    if not _marker_action_required(marker):
        return "none"
    if marker.category == "proof_ready_implementation":
        return (
            "review, merge, or record acceptance for the proof-ready "
            f"implementation at REMAINING_TASKS.md:L{marker.line}"
        )
    if marker.category == "host_side_reference":
        return f"run or attach the host-side evidence referenced at REMAINING_TASKS.md:L{marker.line}"
    return f"produce or record the remaining proof referenced at REMAINING_TASKS.md:L{marker.line}"


def _marker_status(marker: ProofMarker) -> str:
    if marker.category == "proof_ready_implementation":
        text = marker.text.lower()
        if "completed/proof-ready" in text or "not to rebuild completed/proof-ready" in text:
            return "context_only"
        return "open"
    if marker.category == "remaining_proof" and _crypto_edge_remaining_proof_recorded(marker):
        return "satisfied_recorded"
    if marker.category == "remaining_proof" and _remaining_proof_owned_by_passive_lane(marker):
        return "context_only"
    if marker.category != "host_side_reference":
        return "open"
    marker_text = marker.text.lower()
    if any(
        phrase in marker_text
        for phrase in ("remaining", "remain open", "remains open", "still required", "does not close")
    ):
        return "open"
    text = f"{marker.text} {marker.context}".lower()
    recorded_phrases = (
        "host proof recorded",
        "final host proof recorded",
        "read-only hetzner check recorded",
        "read-only refresh recorded",
        "this closes the host-side",
    )
    if any(phrase in text for phrase in recorded_phrases):
        return "satisfied_recorded"
    return "open"


def _crypto_edge_remaining_proof_recorded(marker: ProofMarker) -> bool:
    text = f"{marker.text} {marker.context}".lower()
    if not any(
        phrase in text
        for phrase in (
            "crypto-edge",
            "edge cadence",
            "okx snapshot",
            "okx funding",
            "open-interest",
        )
    ):
        return False
    host_closed = all(
        phrase in text
        for phrase in (
            "final host proof recorded",
            "this closes the host-side crypto-edge schedule/cadence proof",
            "reports fresh okx funding",
            "missing=[]",
            "stale=[]",
        )
    )
    return host_closed


def _remaining_proof_owned_by_passive_lane(marker: ProofMarker) -> bool:
    text = f"{marker.text} {marker.context}".lower()
    passive_owned_phrases = (
        "accepted shadow-derived cost-stack report",
        "backup/restore drill evidence and backup-artifact secrets scan",
        "execute the drill against the future capped-live state bundle",
    )
    return any(phrase in text for phrase in passive_owned_phrases)


def _marker_satisfied(marker: ProofMarker) -> bool:
    return _marker_status(marker).startswith("satisfied")


def _marker_action_required(marker: ProofMarker) -> bool:
    return _marker_status(marker) == "open"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _operator_event_journal_path(root: Path) -> Path:
    return root / ".cbp_state" / "data" / "operator_events" / "operator_events.jsonl"


def _load_operator_events(root: Path) -> list[dict[str, Any]]:
    path = _operator_event_journal_path(root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            raw = json.loads(text)
        except Exception:
            continue
        if isinstance(raw, dict):
            rows.append(raw)
    return rows


def _operator_decision_record_command(target: str, *, result: str = "accepted") -> str:
    return (
        "./.venv/bin/python scripts/record_operator_event.py "
        "--actor operator "
        "--action passive_operator_decision "
        f"--target {target} "
        f"--result {result} "
        "--reason <reason>"
    )


def _operator_decision_event_status(root: Path, *, target: str) -> dict[str, Any]:
    path = _operator_event_journal_path(root)
    accepted_results = {"accepted", "accepted_with_risk", "declined", "no_persistent_campaign", "research_only"}
    matches = [
        row
        for row in _load_operator_events(root)
        if str(row.get("action") or "") == "passive_operator_decision"
        and str(row.get("target") or "") == target
        and str(row.get("result") or "") in accepted_results
    ]
    if not matches:
        return {
            "artifact_id": "operator_decision_event",
            "artifact_path": str(path),
            "artifact_exists": path.is_file(),
            "artifact_sha256": _sha256(path),
            "target": target,
            "artifact_status": "missing",
            "satisfied": False,
            "accepted_results": sorted(accepted_results),
            "record_command": _operator_decision_record_command(target),
        }
    latest = matches[-1]
    return {
        "artifact_id": "operator_decision_event",
        "artifact_path": str(path),
        "artifact_exists": path.is_file(),
        "artifact_sha256": _sha256(path),
        "target": target,
        "artifact_status": "recorded",
        "accepted_results": sorted(accepted_results),
        "event_id": latest.get("event_id"),
        "timestamp": latest.get("timestamp"),
        "result": latest.get("result"),
        "reason": latest.get("reason"),
        "satisfied": True,
    }


def _pullback_stage0_artifact_status(root: Path) -> dict[str, Any]:
    latest = (
        root
        / ".cbp_state"
        / "data"
        / "pullback_stage0_verification"
        / "pullback_stage0_verification.latest.json"
    )
    payload = _load_json(latest)
    passed = (
        latest.is_file()
        and str(payload.get("report_type") or "") == "pullback_stage0_verification"
        and str(payload.get("status") or "") == "passed"
        and int(payload.get("blocking_checks") or 0) == 0
        and bool(payload.get("read_only")) is True
        and str(payload.get("strategy") or "") == "pullback_recovery"
        and str(payload.get("session_strategy_id") or "") == "pullback_recovery_default"
    )
    return {
        "artifact_id": "pullback_stage0_verification",
        "artifact_path": str(latest),
        "artifact_exists": latest.is_file(),
        "artifact_sha256": _sha256(latest),
        "artifact_status": str(payload.get("status") or "missing"),
        "satisfied": bool(passed),
    }


def _paper_gate_velocity_artifact_status(root: Path) -> dict[str, Any]:
    latest = root / ".cbp_state" / "data" / "paper_gate_velocity" / "paper_gate_velocity.latest.json"
    payload = _load_json(latest)
    round_trips = payload.get("round_trips") if isinstance(payload.get("round_trips"), dict) else {}
    qualified_bars = (
        payload.get("qualified_bars") if isinstance(payload.get("qualified_bars"), dict) else {}
    )
    passed = (
        latest.is_file()
        and str(payload.get("report_type") or "") == "paper_gate_velocity"
        and bool(payload.get("ok")) is True
        and bool(payload.get("read_only")) is True
        and str(payload.get("strategy_id") or "") == "es_daily_trend_v1"
        and "qualified" in round_trips
        and "recorded" in qualified_bars
    )
    return {
        "artifact_id": "paper_gate_velocity",
        "artifact_path": str(latest),
        "artifact_exists": latest.is_file(),
        "artifact_sha256": _sha256(latest),
        "artifact_status": "recorded" if passed else str(payload.get("status") or "missing"),
        "generated_at": str(payload.get("generated_at") or ""),
        "satisfied": bool(passed),
    }


def _cost_assumptions_artifact_status(root: Path) -> dict[str, Any]:
    latest = root / ".cbp_state" / "data" / "cost_assumptions" / "cost_assumptions.latest.json"
    payload = _load_json(latest)
    passed = (
        latest.is_file()
        and str(payload.get("report_type") or "") == "cost_assumptions"
        and bool(payload.get("read_only")) is True
        and str(payload.get("overall") or "") in {"ok", "warning"}
        and isinstance(payload.get("checks"), list)
        and bool(payload.get("checks"))
    )
    return {
        "artifact_id": "cost_assumptions",
        "artifact_path": str(latest),
        "artifact_exists": latest.is_file(),
        "artifact_sha256": _sha256(latest),
        "artifact_status": str(payload.get("overall") or "missing"),
        "generated_at": str(payload.get("generated_at") or ""),
        "satisfied": bool(passed),
    }


def _research_inventory_row(root: Path, artifact_id: str) -> dict[str, Any]:
    try:
        from services.analytics.research_artifact_inventory import build_research_artifact_inventory
    except Exception:
        return {}
    report = build_research_artifact_inventory(repo_root=root, artifact_id=artifact_id)
    rows = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []
    if not rows or not isinstance(rows[0], dict):
        return {}
    return rows[0]


def _research_row_ok(row: dict[str, Any], *, terminal_ok: bool = False) -> bool:
    status = str(row.get("latest_status") or "")
    if status == "latest_ok":
        return True
    return bool(terminal_ok and status == "latest_terminal_no_candidates")


def _archive_research_artifact_status(root: Path) -> dict[str, Any]:
    required = {
        "archive_walk_forward": _research_inventory_row(root, "archive_walk_forward"),
        "archive_parameter_sweep": _research_inventory_row(root, "archive_parameter_sweep"),
        "archive_parameter_sweep_triage": _research_inventory_row(root, "archive_parameter_sweep_triage"),
    }
    satisfied = (
        _research_row_ok(required["archive_walk_forward"])
        and _research_row_ok(required["archive_parameter_sweep"])
        and _research_row_ok(required["archive_parameter_sweep_triage"], terminal_ok=True)
    )
    return {
        "artifact_id": "archive_research_evidence",
        "artifact_status": "recorded" if satisfied else "missing_or_incomplete",
        "satisfied": bool(satisfied),
        "artifacts": [
            {
                "artifact_id": artifact_id,
                "latest_status": str(row.get("latest_status") or "missing"),
                "latest_path": row.get("latest_path"),
                "latest_sha256": row.get("latest_sha256"),
            }
            for artifact_id, row in required.items()
        ],
    }


def _funding_research_artifact_status(root: Path) -> dict[str, Any]:
    required = {
        "funding_threshold_pipeline_summary": _research_inventory_row(root, "funding_threshold_pipeline_summary"),
        "funding_context_price_join": _research_inventory_row(root, "funding_context_price_join"),
        "funding_threshold_candidate_triage": _research_inventory_row(root, "funding_threshold_candidate_triage"),
    }
    candidate_row = required["funding_threshold_candidate_triage"]
    candidate_payload = _load_json(Path(str(candidate_row.get("latest_path") or "")))
    candidates = candidate_payload.get("review_candidates")
    if not isinstance(candidates, list):
        candidates = candidate_payload.get("candidates") if isinstance(candidate_payload.get("candidates"), list) else []
    actionable_candidates = [
        row for row in candidates if isinstance(row, dict) and str(row.get("status") or "") == "candidate"
    ]
    evidence_recorded = all(_research_row_ok(row) for row in required.values())
    actionable_basis = bool(actionable_candidates)
    decision_event = _operator_decision_event_status(root, target="funding_extreme_persistent_campaign_decision")
    decision_satisfied = bool(decision_event.get("satisfied"))
    return {
        "artifact_id": "funding_research_evidence",
        "artifact_status": (
            "decision_recorded"
            if decision_satisfied
            else "actionable_basis_recorded"
            if evidence_recorded and actionable_basis
            else "no_actionable_basis"
            if evidence_recorded
            else "missing_or_incomplete"
        ),
        "satisfied": decision_satisfied,
        "evidence_recorded": bool(evidence_recorded),
        "actionable_basis": bool(actionable_basis),
        "candidate_count": len(actionable_candidates),
        "decision_event": decision_event,
        "next_action": (
            "none"
            if decision_satisfied
            else _operator_decision_record_command("funding_extreme_persistent_campaign_decision")
            if evidence_recorded and actionable_basis
            else _operator_decision_record_command(
                "funding_extreme_persistent_campaign_decision",
                result="no_persistent_campaign",
            )
            if evidence_recorded
            else "run or repair the funding threshold research pipeline"
        ),
        "artifacts": [
            {
                "artifact_id": artifact_id,
                "latest_status": str(row.get("latest_status") or "missing"),
                "latest_path": row.get("latest_path"),
                "latest_sha256": row.get("latest_sha256"),
            }
            for artifact_id, row in required.items()
        ],
    }


def _passive_artifact_status(root: Path, item: str) -> dict[str, Any] | None:
    if "Canonical `es_daily_trend_v1` qualified round-trip collection" in item:
        return _paper_gate_velocity_artifact_status(root)
    if "Pullback Stage 0 long proof" in item:
        return _pullback_stage0_artifact_status(root)
    if "Manual strategy performance decision" in item:
        out = _operator_decision_event_status(root, target="manual_strategy_performance_decision")
        if not bool(out.get("satisfied")):
            out["next_action"] = str(out.get("record_command") or "")
        return out
    if "Composite/hybrid paper advancement decision" in item:
        out = _operator_decision_event_status(root, target="composite_hybrid_paper_advancement_decision")
        if not bool(out.get("satisfied")):
            out["next_action"] = str(out.get("record_command") or "")
        return out
    if "Real multi-year archive sweeps" in item:
        return _archive_research_artifact_status(root)
    if "`funding_extreme` persistent-campaign decision" in item:
        return _funding_research_artifact_status(root)
    return None


def _marker_artifact_status(root: Path, marker: ProofMarker) -> dict[str, Any] | None:
    text = f"{marker.text} {marker.context}".lower()
    if marker.category == "remaining_operational_proof" and (
        "fee/slippage" in text or "cost-assumption" in text or "cost assumptions" in text
    ):
        return _cost_assumptions_artifact_status(root)
    return None


def _marker_row(root: Path, marker: ProofMarker) -> dict[str, Any]:
    artifact_status = _marker_artifact_status(root, marker)
    artifact_satisfied = bool((artifact_status or {}).get("satisfied"))
    status = "satisfied_artifact" if artifact_satisfied else _marker_status(marker)
    action_required = False if artifact_satisfied else _marker_action_required(marker)
    return {
        "line": marker.line,
        "category": marker.category,
        "marker": marker.marker,
        "text": marker.text,
        "status": status,
        "satisfied": artifact_satisfied or _marker_satisfied(marker),
        "action_required": action_required,
        "next_action": "none" if artifact_satisfied else _marker_next_action(marker),
        "artifact_status": artifact_status,
    }


def build_operator_proof_status(
    *,
    repo_root: str | Path | None = None,
    category: str | None = None,
    line: int | str | None = None,
    passive_ordinal: int | str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    category_filter = str(category or "").strip()
    line_filter: int | None = None
    line_filter_raw = str(line or "").strip()
    valid_line_filter = True
    if line_filter_raw:
        try:
            line_filter = int(line_filter_raw)
        except Exception:
            valid_line_filter = False
        else:
            if line_filter <= 0:
                valid_line_filter = False
    passive_ordinal_filter: int | None = None
    passive_ordinal_raw = str(passive_ordinal or "").strip()
    valid_passive_ordinal_filter = True
    if passive_ordinal_raw:
        try:
            passive_ordinal_filter = int(passive_ordinal_raw)
        except Exception:
            valid_passive_ordinal_filter = False
        else:
            if passive_ordinal_filter <= 0:
                valid_passive_ordinal_filter = False
    lane_doc = root / "docs" / "BACKLOG_EXECUTION_LANES.md"
    backlog = root / "REMAINING_TASKS.md"
    lane_text = _read_text(lane_doc)
    backlog_text = _read_text(backlog)
    all_passive_items = _bullet_items(_section(lane_text, PASSIVE_HEADING))
    passive_rows: list[dict[str, Any]] = []
    for idx, item in enumerate(all_passive_items, start=1):
        artifact_status = _passive_artifact_status(root, item)
        satisfied = bool((artifact_status or {}).get("satisfied"))
        artifact_next_action = str((artifact_status or {}).get("next_action") or "")
        passive_rows.append(
            {
                "ordinal": idx,
                "text": item,
                "action_required": not satisfied,
                "next_action": (
                    "none"
                    if satisfied
                    else artifact_next_action
                    if artifact_next_action
                    else f"collect or record operator evidence: {item}"
                ),
                "artifact_status": artifact_status,
            }
        )
    if valid_passive_ordinal_filter and passive_ordinal_filter is not None:
        passive_rows = [row for row in passive_rows if int(row.get("ordinal") or 0) == passive_ordinal_filter]
        if not passive_rows:
            valid_passive_ordinal_filter = False
    all_proof_markers = _proof_markers(backlog_text)
    source_category_counts = _category_counts(all_proof_markers)
    available_categories = tuple(sorted(source_category_counts))
    valid_category_filter = not category_filter or category_filter in source_category_counts
    proof_markers = all_proof_markers
    proof_marker_scope = "all"
    if category_filter and valid_category_filter:
        proof_markers = tuple(marker for marker in all_proof_markers if marker.category == category_filter)
        proof_marker_scope = "category"
    elif category_filter:
        proof_markers = ()
        proof_marker_scope = "category"
    if valid_line_filter and line_filter is not None:
        proof_markers = tuple(marker for marker in proof_markers if marker.line == line_filter)
        proof_marker_scope = "line" if proof_marker_scope == "all" else f"{proof_marker_scope}+line"
    passive_ordinal_requested = bool(passive_ordinal_raw)
    explicit_proof_filter_requested = bool(category_filter) or bool(line_filter_raw)
    if passive_ordinal_requested and not explicit_proof_filter_requested:
        # A passive-ordinal query is a focused passive-lane report. Preserve
        # source counts for auditability, but avoid dumping unrelated backlog
        # proof markers into the focused operator action output.
        proof_markers = ()
        proof_marker_scope = "suppressed_by_passive_ordinal"
    category_counts = _category_counts(proof_markers)
    proof_marker_rows = [_marker_row(root, marker) for marker in proof_markers]
    remaining_marker_count = sum(
        count
        for category, count in category_counts.items()
        if category.startswith("remaining_")
    )
    ok = bool(
        lane_text
        and backlog_text
        and all_passive_items
        and valid_category_filter
        and valid_line_filter
        and valid_passive_ordinal_filter
    )
    reason: str | None = None
    if not valid_category_filter:
        reason = "invalid_category"
    elif not valid_line_filter:
        reason = "invalid_line"
    elif not valid_passive_ordinal_filter:
        reason = "invalid_passive_operator_ordinal"

    return {
        "schema_version": 1,
        "report_type": "operator_proof_status",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "read_only": True,
        "planning_only": True,
        "does_not_close_proof": True,
        "does_not_run_campaigns": True,
        "does_not_fetch_market_data": True,
        "does_not_mutate_state": True,
        "repo_root": str(root),
        "category_filter": category_filter or None,
        "available_categories": list(available_categories),
        "line_filter": line_filter if valid_line_filter else None,
        "passive_operator_ordinal_filter": passive_ordinal_filter if valid_passive_ordinal_filter else None,
        "lane_doc": str(lane_doc),
        "lane_doc_sha256": _sha256(lane_doc),
        "backlog": str(backlog),
        "backlog_sha256": _sha256(backlog),
        "passive_operator_item_count": len(passive_rows),
        "source_passive_operator_item_count": len(all_passive_items),
        "passive_operator_items": passive_rows,
        "proof_marker_scope": proof_marker_scope,
        "proof_marker_count": len(proof_markers),
        "source_proof_marker_count": len(all_proof_markers),
        "proof_markers": proof_marker_rows,
        "summary": {
            "passive_operator_items": len(passive_rows),
            "source_passive_operator_items": len(all_passive_items),
            "passive_operator_items_satisfied": sum(1 for row in passive_rows if not bool(row.get("action_required"))),
            "remaining_proof_or_coverage_markers": remaining_marker_count,
            "host_side_markers": category_counts.get("host_side_reference", 0),
            "proof_ready_markers": category_counts.get("proof_ready_implementation", 0),
            "proof_marker_actions_required": sum(1 for row in proof_marker_rows if bool(row.get("action_required"))),
            "proof_markers_satisfied": sum(1 for row in proof_marker_rows if bool(row.get("satisfied"))),
            "proof_markers_context_only": sum(1 for row in proof_marker_rows if row.get("status") == "context_only"),
            "category_counts": category_counts,
            "source_category_counts": source_category_counts,
        },
        "reason": reason,
    }
