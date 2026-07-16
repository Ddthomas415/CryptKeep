from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from services.audit.operator_event_journal import append_operator_event

_LOG = logging.getLogger(__name__)


def _artifact_names(paths: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for value in paths.values():
        try:
            names.append(Path(str(value)).name)
        except Exception:
            continue
    return sorted(name for name in names if name)


def _status_value(report: dict[str, Any]) -> str:
    for key in ("severity", "status", "decision", "result"):
        value = str(report.get(key) or "").strip()
        if value:
            return value[:80]
    if "ok" in report:
        return "ok" if bool(report.get("ok")) else "not_ok"
    return "unknown"


def record_ai_copilot_report_write(
    *,
    report_type: str,
    report: dict[str, Any],
    paths: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    """Append a metadata-only operator event for persisted AI copilot reports."""
    normalized_report_type = str(report_type or "unknown").strip() or "unknown"
    path_keys = sorted(str(key) for key in paths.keys())
    try:
        event = append_operator_event(
            actor="system",
            action="ai_copilot_report_write",
            target=f"ai_copilot_report:{normalized_report_type}",
            result="success",
            reason="write_report_artifacts",
            pre_state={"report_type": normalized_report_type},
            post_state={
                "report_type": normalized_report_type,
                "status": _status_value(report),
                "artifact_count": len(path_keys),
                "artifact_keys": path_keys,
                "artifact_names": _artifact_names(paths),
            },
            source=source,
            extra={"report_payload_logged": False, "artifact_content_logged": False},
        )
        return {"ok": True, "event_id": event.get("event_id"), "path": event.get("path")}
    except Exception as exc:
        _LOG.warning(
            "AI copilot report-write operator event journal failed: %s: %s",
            type(exc).__name__,
            exc,
        )
        return {"ok": False, "reason": f"operator_event_write_failed:{type(exc).__name__}"}
