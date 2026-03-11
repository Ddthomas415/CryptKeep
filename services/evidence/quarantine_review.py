from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

from services.evidence.ingest import ingest_event
from storage.evidence_signals_sqlite import EvidenceSignalsSQLite


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_queue(limit: int = 200, status: str | None = "queued") -> Dict[str, Any]:
    store = EvidenceSignalsSQLite()
    rows = store.recent_quarantine(limit=int(limit), status=status)
    return {"ok": True, "rows": rows, "count": len(rows)}


def reject_quarantine(quarantine_id: str, *, reason: str | None = None) -> Dict[str, Any]:
    store = EvidenceSignalsSQLite()
    row = store.get_quarantine(quarantine_id)
    if not row:
        return {"ok": False, "reason": "quarantine_not_found", "quarantine_id": quarantine_id}
    store.update_quarantine(quarantine_id, status="rejected", reviewed_ts=_now_iso())
    return {"ok": True, "quarantine_id": quarantine_id, "status": "rejected", "reason": reason}


def normalize_quarantine(
    quarantine_id: str,
    *,
    normalized_event: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    store = EvidenceSignalsSQLite()
    row = store.get_quarantine(quarantine_id)
    if not row:
        return {"ok": False, "reason": "quarantine_not_found", "quarantine_id": quarantine_id}

    payload = {}
    try:
        payload_raw = row.get("payload_json")
        payload = json.loads(payload_raw) if isinstance(payload_raw, str) else {}
    except Exception:
        payload = {}
    merged = dict(payload)
    merged.update(dict(normalized_event or {}))

    out = ingest_event(
        merged,
        source_id=str(row.get("source_id") or ""),
        source_type="manual",
        display_name="Quarantine Review",
        consent_confirmed=True,
    )
    if not out.get("ok"):
        return {"ok": False, "reason": "normalization_failed", "quarantine_id": quarantine_id, "result": out}

    store.update_quarantine(
        quarantine_id,
        status="normalized",
        reviewed_ts=_now_iso(),
        normalized_signal_id=str(out.get("signal_id") or ""),
    )
    return {"ok": True, "quarantine_id": quarantine_id, "status": "normalized", "result": out}
