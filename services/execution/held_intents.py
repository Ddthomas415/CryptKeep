from __future__ import annotations

from typing import Any, Dict, List

from storage.intent_queue_sqlite import IntentQueueSQLite


def hold_intent(intent_id: str, *, reason: str = "manual_hold") -> Dict[str, Any]:
    db = IntentQueueSQLite()
    row = db.get_intent(str(intent_id))
    if not row:
        return {"ok": False, "reason": "intent_not_found", "intent_id": str(intent_id)}
    db.update_status(str(intent_id), "held", last_error=str(reason))
    return {"ok": True, "intent_id": str(intent_id), "status": "held", "reason": str(reason)}


def release_intent(intent_id: str) -> Dict[str, Any]:
    db = IntentQueueSQLite()
    row = db.get_intent(str(intent_id))
    if not row:
        return {"ok": False, "reason": "intent_not_found", "intent_id": str(intent_id)}
    db.update_status(str(intent_id), "queued", last_error=None)
    return {"ok": True, "intent_id": str(intent_id), "status": "queued"}


def list_held(*, limit: int = 200) -> List[Dict[str, Any]]:
    return IntentQueueSQLite().list_intents(limit=int(limit), status="held")
