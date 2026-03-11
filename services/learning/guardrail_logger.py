# Phase 185: Learning guardrail logging + metrics
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from storage.execution_report_sqlite import ExecutionReportSQLite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_guardrail_event(
    *,
    event: str,
    status: str,
    payload: Dict[str, Any] | None = None,
    report_id: str | None = None,
) -> Dict[str, Any]:
    rid = str(report_id or f"guardrail-{uuid.uuid4()}")
    body = {"kind": "learning_guardrail", "event": str(event), "status": str(status), "payload": dict(payload or {})}
    ExecutionReportSQLite().add_report(
        {
            "report_id": rid,
            "ts": _now(),
            "status": str(status),
            "summary": f"learning_guardrail:{event}",
            "payload": body,
        }
    )
    return {"ok": True, "report_id": rid}
