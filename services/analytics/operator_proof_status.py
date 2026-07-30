from __future__ import annotations

import hashlib
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
    for line_no, raw in enumerate(backlog_text.splitlines(), start=1):
        text = raw.strip()
        if not text:
            continue
        lowered = text.lower()
        for category, marker in _MARKERS:
            if marker in lowered:
                markers.append(
                    ProofMarker(
                        line=line_no,
                        category=category,
                        marker=marker,
                        text=text,
                    )
                )
                break
    return tuple(markers)


def _category_counts(markers: tuple[ProofMarker, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for marker in markers:
        out[marker.category] = out.get(marker.category, 0) + 1
    return out


def _marker_next_action(marker: ProofMarker) -> str:
    if marker.category == "proof_ready_implementation":
        return (
            "review, merge, or record acceptance for the proof-ready "
            f"implementation at REMAINING_TASKS.md:L{marker.line}"
        )
    if marker.category == "host_side_reference":
        return f"run or attach the host-side evidence referenced at REMAINING_TASKS.md:L{marker.line}"
    return f"produce or record the remaining proof referenced at REMAINING_TASKS.md:L{marker.line}"


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
    passive_rows = [
        {
            "ordinal": idx,
            "text": item,
            "action_required": True,
            "next_action": f"collect or record operator evidence: {item}",
        }
        for idx, item in enumerate(all_passive_items, start=1)
    ]
    if valid_passive_ordinal_filter and passive_ordinal_filter is not None:
        passive_rows = [row for row in passive_rows if int(row.get("ordinal") or 0) == passive_ordinal_filter]
        if not passive_rows:
            valid_passive_ordinal_filter = False
    all_proof_markers = _proof_markers(backlog_text)
    source_category_counts = _category_counts(all_proof_markers)
    available_categories = tuple(sorted(source_category_counts))
    valid_category_filter = not category_filter or category_filter in source_category_counts
    proof_markers = all_proof_markers
    if category_filter and valid_category_filter:
        proof_markers = tuple(marker for marker in all_proof_markers if marker.category == category_filter)
    elif category_filter:
        proof_markers = ()
    if valid_line_filter and line_filter is not None:
        proof_markers = tuple(marker for marker in proof_markers if marker.line == line_filter)
    category_counts = _category_counts(proof_markers)
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
        "proof_marker_count": len(proof_markers),
        "source_proof_marker_count": len(all_proof_markers),
        "proof_markers": [
            {
                "line": marker.line,
                "category": marker.category,
                "marker": marker.marker,
                "text": marker.text,
                "action_required": True,
                "next_action": _marker_next_action(marker),
            }
            for marker in proof_markers
        ],
        "summary": {
            "passive_operator_items": len(passive_rows),
            "source_passive_operator_items": len(all_passive_items),
            "remaining_proof_or_coverage_markers": remaining_marker_count,
            "host_side_markers": category_counts.get("host_side_reference", 0),
            "proof_ready_markers": category_counts.get("proof_ready_implementation", 0),
            "category_counts": category_counts,
            "source_category_counts": source_category_counts,
        },
        "reason": reason,
    }
