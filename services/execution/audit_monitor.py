from __future__ import annotations

from collections import Counter
from typing import Any, Dict

from services.execution.intent_audit import recent_intent_events


def summarize_intent_audit(*, limit: int = 500) -> Dict[str, Any]:
    rows = recent_intent_events(limit=int(limit))
    by_status = Counter()
    by_event = Counter()
    for r in rows:
        payload = r.get("payload") if isinstance(r.get("payload"), dict) else {}
        by_status[str(payload.get("status") or r.get("status") or "unknown")] += 1
        by_event[str(payload.get("event") or "unknown")] += 1

    total = len(rows)
    failed = int(by_status.get("failed", 0) + by_status.get("error", 0))
    fail_ratio = (failed / total) if total > 0 else 0.0
    severity = "ok"
    if fail_ratio >= 0.25 and total >= 8:
        severity = "high"
    elif fail_ratio >= 0.1 and total >= 5:
        severity = "warn"
    return {
        "ok": True,
        "count": total,
        "failed": failed,
        "fail_ratio": float(fail_ratio),
        "severity": severity,
        "by_status": dict(by_status),
        "by_event": dict(by_event),
    }
