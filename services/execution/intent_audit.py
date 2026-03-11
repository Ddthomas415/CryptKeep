from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from storage.execution_report_sqlite import ExecutionReportSQLite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_intent_event(
    *,
    intent_id: str,
    event: str,
    status: str,
    venue: str | None = None,
    symbol: str | None = None,
    details: Dict[str, Any] | None = None,
    report_id: str | None = None,
) -> Dict[str, Any]:
    rid = str(report_id or f"intent-{uuid.uuid4()}")
    payload = {
        "kind": "intent_audit",
        "intent_id": str(intent_id),
        "event": str(event),
        "status": str(status),
        "details": dict(details or {}),
    }
    out = ExecutionReportSQLite().add_report(
        {
            "report_id": rid,
            "ts": _now(),
            "venue": venue,
            "symbol": symbol,
            "status": str(status),
            "summary": f"{event}:{status}",
            "payload": payload,
        }
    )
    return {"ok": True, "report_id": rid, **out}


def recent_intent_events(*, limit: int = 200, venue: str | None = None, symbol: str | None = None) -> List[Dict[str, Any]]:
    rows = ExecutionReportSQLite().recent(limit=int(limit), venue=venue, symbol=symbol)
    out: list[dict[str, Any]] = []
    for r in rows:
        p = r.get("payload") if isinstance(r.get("payload"), dict) else {}
        if p.get("kind") != "intent_audit":
            continue
        out.append(r)
    return out
