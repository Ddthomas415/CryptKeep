from __future__ import annotations

from typing import Any, Dict, List

from services.execution import state_authority
from services.execution.state_authority import LiveStateContext
from storage.intent_queue_sqlite import IntentQueueSQLite


def hold_intent(intent_id: str, *, reason: str = "manual_hold") -> Dict[str, Any]:
    db = IntentQueueSQLite()
    row = db.get_intent(str(intent_id))
    if not row:
        return {"ok": False, "reason": "intent_not_found", "intent_id": str(intent_id)}
    ctx = LiveStateContext(authority="INTENT_CONSUMER", origin="hold")
    state_authority.paper_queue_hold_release(db, row, "held", ctx=ctx, reason=str(reason))
    return {"ok": True, "intent_id": str(intent_id), "status": "held", "reason": str(reason)}


def release_intent(intent_id: str) -> Dict[str, Any]:
    db = IntentQueueSQLite()
    row = db.get_intent(str(intent_id))
    if not row:
        return {"ok": False, "reason": "intent_not_found", "intent_id": str(intent_id)}
    ctx = LiveStateContext(authority="INTENT_CONSUMER", origin="release")
    state_authority.paper_queue_hold_release(db, row, "queued", ctx=ctx)
    return {"ok": True, "intent_id": str(intent_id), "status": "queued"}


def list_held(*, limit: int = 200) -> List[Dict[str, Any]]:
    return IntentQueueSQLite().list_intents(limit=int(limit), status="held")
