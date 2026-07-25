from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LANE_HEADINGS: tuple[str, ...] = (
    "Passive / Operator Evidence",
    "Low-Risk Docs / Tests",
    "Medium-Risk Runtime / Read-Only",
    "High-Risk Gate / Execution / Deploy",
)


@dataclass(frozen=True)
class LaneSummary:
    name: str
    item_count: int
    items: tuple[str, ...]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
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


def _lane_summary(text: str, heading: str) -> LaneSummary:
    items = _bullet_items(_section(text, heading))
    return LaneSummary(name=heading, item_count=len(items), items=items)


def build_backlog_lane_status(*, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    lane_doc = root / "docs" / "BACKLOG_EXECUTION_LANES.md"
    backlog = root / "REMAINING_TASKS.md"
    lane_text = _read_text(lane_doc)
    backlog_text = _read_text(backlog)
    lanes = [_lane_summary(lane_text, heading) for heading in LANE_HEADINGS]
    missing_lanes = [lane.name for lane in lanes if lane.item_count == 0]
    backlog_links_lane_doc = "docs/BACKLOG_EXECUTION_LANES.md" in backlog_text
    ok = bool(lane_text and backlog_text and not missing_lanes and backlog_links_lane_doc)

    return {
        "schema_version": 1,
        "report_type": "backlog_lane_status",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "read_only": True,
        "planning_only": True,
        "does_not_decide_backlog_items": True,
        "repo_root": str(root),
        "source_doc": str(lane_doc),
        "source_doc_sha256": _sha256(lane_doc),
        "backlog": str(backlog),
        "backlog_sha256": _sha256(backlog),
        "backlog_links_lane_doc": backlog_links_lane_doc,
        "lane_count": len(lanes),
        "total_item_count": sum(lane.item_count for lane in lanes),
        "missing_lanes": missing_lanes,
        "lanes": [
            {
                "name": lane.name,
                "item_count": lane.item_count,
                "items": list(lane.items),
            }
            for lane in lanes
        ],
        "summary": {
            "passive_operator_evidence": lanes[0].item_count,
            "low_risk_docs_tests": lanes[1].item_count,
            "medium_risk_runtime_read_only": lanes[2].item_count,
            "high_risk_gate_execution_deploy": lanes[3].item_count,
        },
    }
