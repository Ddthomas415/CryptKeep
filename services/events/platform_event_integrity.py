from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.events.platform_event_journal import (
    SCHEMA_VERSION,
    SUPPORTED_EVENT_TYPES,
    platform_event_journal_path,
)

REQUIRED_FIELDS = (
    "schema_version",
    "event_id",
    "timestamp",
    "event_type",
    "producer",
    "source",
    "commit_sha",
    "provenance",
    "payload",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _present_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def _timestamp_ok(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def _event_findings(row: Any, *, line: int, event_index: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(row, dict):
        return [{"line": line, "event_index": event_index, "reason": "event_not_object"}]

    for field in REQUIRED_FIELDS:
        if field not in row:
            findings.append({"line": line, "event_index": event_index, "reason": f"missing_field:{field}"})

    if row.get("schema_version") != SCHEMA_VERSION:
        findings.append({"line": line, "event_index": event_index, "reason": "invalid_schema_version"})
    if not _present_text(row.get("event_id")):
        findings.append({"line": line, "event_index": event_index, "reason": "missing_event_id"})
    if not _timestamp_ok(row.get("timestamp")):
        findings.append({"line": line, "event_index": event_index, "reason": "invalid_timestamp"})
    if row.get("event_type") not in SUPPORTED_EVENT_TYPES:
        findings.append({"line": line, "event_index": event_index, "reason": "unsupported_event_type"})
    if not _present_text(row.get("producer")):
        findings.append({"line": line, "event_index": event_index, "reason": "missing_producer"})
    if not _present_text(row.get("source")):
        findings.append({"line": line, "event_index": event_index, "reason": "missing_source"})
    if not _present_text(row.get("commit_sha")):
        findings.append({"line": line, "event_index": event_index, "reason": "missing_commit_sha"})
    if not isinstance(row.get("provenance"), dict):
        findings.append({"line": line, "event_index": event_index, "reason": "invalid_provenance"})
    if not isinstance(row.get("payload"), dict):
        findings.append({"line": line, "event_index": event_index, "reason": "invalid_payload"})
    return findings


def check_platform_event_integrity(
    path: Path | None = None,
    *,
    require_events: bool = False,
) -> dict[str, Any]:
    src = Path(path) if path is not None else platform_event_journal_path()
    findings: list[dict[str, Any]] = []
    event_count = 0

    if not src.exists():
        if require_events:
            findings.append({"reason": "platform_event_journal_missing", "path": str(src)})
        return {
            "created": _utc_now(),
            "ok": not findings,
            "path": str(src),
            "exists": False,
            "event_count": 0,
            "finding_count": len(findings),
            "findings": findings,
        }

    with src.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            text = raw.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except Exception as exc:
                findings.append(
                    {
                        "line": line_no,
                        "reason": "platform_event_json_unparseable",
                        "error": type(exc).__name__,
                    }
                )
                continue
            event_count += 1
            findings.extend(_event_findings(row, line=line_no, event_index=event_count - 1))

    if require_events and event_count == 0:
        findings.append({"reason": "platform_event_journal_empty", "path": str(src)})

    return {
        "created": _utc_now(),
        "ok": not findings,
        "path": str(src),
        "exists": True,
        "event_count": event_count,
        "finding_count": len(findings),
        "findings": findings,
    }

