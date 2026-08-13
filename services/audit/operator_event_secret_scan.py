from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.audit.jsonl_secret_scan import scan_jsonl_secret_fields
from services.audit.operator_event_journal import operator_event_journal_path


def _action_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            text = raw.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except Exception:
                continue
            action = str(row.get("action") or "").strip()
            if action:
                counts[action] = counts.get(action, 0) + 1
    return counts


def scan_operator_event_journal(
    path: Path | None = None,
    *,
    require_events: bool = False,
    require_actions: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    src = Path(path) if path is not None else operator_event_journal_path()
    report = scan_jsonl_secret_fields(
        src,
        require_events=require_events,
        missing_reason="operator_event_journal_missing",
        empty_reason="operator_event_journal_empty",
        json_reason="operator_event_json_unparseable",
    )
    required = [str(action).strip() for action in (require_actions or []) if str(action).strip()]
    if required:
        counts = _action_counts(src)
        report["required_actions"] = required
        report["action_counts"] = {action: counts.get(action, 0) for action in required}
        findings = list(report.get("findings") or [])
        for action in required:
            if counts.get(action, 0) <= 0:
                findings.append({"reason": "operator_event_required_action_missing", "action": action})
        report["findings"] = findings
        report["finding_count"] = len(findings)
        report["ok"] = not findings
    return report
