from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.audit.operator_event_journal import (
    SENSITIVE_KEY_PARTS,
    operator_event_journal_path,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_sensitive_key(key: Any) -> bool:
    lowered = str(key).lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def _is_safely_redacted(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in ("", "<redacted>")
    return False


def _value_summary(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return {"type": "str", "length": len(value)}
    if isinstance(value, (int, float, bool)) or value is None:
        return {"type": type(value).__name__}
    if isinstance(value, list):
        return {"type": "list", "length": len(value)}
    if isinstance(value, dict):
        return {"type": "dict", "keys": len(value)}
    return {"type": type(value).__name__}


def _scan_value(value: Any, *, path: str, event_index: int, findings: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            child_path = f"{path}.{key}" if path else key
            if _is_sensitive_key(key):
                if not _is_safely_redacted(raw_value):
                    findings.append(
                        {
                            "event_index": event_index,
                            "path": child_path,
                            "reason": "sensitive_key_unredacted",
                            "value": _value_summary(raw_value),
                        }
                    )
                continue
            _scan_value(raw_value, path=child_path, event_index=event_index, findings=findings)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_value(item, path=f"{path}[{idx}]", event_index=event_index, findings=findings)


def scan_operator_event_journal(path: Path | None = None, *, require_events: bool = False) -> dict[str, Any]:
    src = Path(path) if path is not None else operator_event_journal_path()
    findings: list[dict[str, Any]] = []
    event_count = 0

    if not src.exists():
        if require_events:
            findings.append({"reason": "operator_event_journal_missing", "path": str(src)})
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
                event = json.loads(text)
            except Exception as exc:
                findings.append(
                    {
                        "line": line_no,
                        "reason": "operator_event_json_unparseable",
                        "error": type(exc).__name__,
                    }
                )
                continue
            event_count += 1
            _scan_value(event, path="", event_index=event_count - 1, findings=findings)

    if require_events and event_count == 0:
        findings.append({"reason": "operator_event_journal_empty", "path": str(src)})

    return {
        "created": _utc_now(),
        "ok": not findings,
        "path": str(src),
        "exists": True,
        "event_count": event_count,
        "finding_count": len(findings),
        "findings": findings,
    }
