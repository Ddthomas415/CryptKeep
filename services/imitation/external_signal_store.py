from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from storage.signal_inbox_sqlite import SignalInboxSQLite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExternalSignalStore:
    def __init__(self, store: SignalInboxSQLite | None = None) -> None:
        self.store = store or SignalInboxSQLite()

    def add_signal(
        self,
        *,
        source: str,
        author: str,
        symbol: str,
        action: str,
        confidence: float = 0.5,
        notes: str | None = None,
        venue_hint: str | None = None,
        raw: Dict[str, Any] | None = None,
        signal_id: str | None = None,
        ts: str | None = None,
    ) -> Dict[str, Any]:
        sid = str(signal_id or uuid.uuid4())
        row = {
            "signal_id": sid,
            "ts": str(ts or _now()),
            "received_ts": _now(),
            "source": str(source or "external"),
            "author": str(author or "unknown"),
            "venue_hint": (None if venue_hint is None else str(venue_hint)),
            "symbol": str(symbol),
            "action": str(action).lower().strip(),
            "confidence": float(confidence),
            "notes": notes,
            "raw": dict(raw or {}),
            "status": "new",
        }
        self.store.upsert_signal(row)
        return {"ok": True, "signal_id": sid}

    def recent(self, *, limit: int = 200, symbol: str | None = None) -> List[Dict[str, Any]]:
        return self.store.list_signals(limit=int(limit), status=None, symbol=symbol)
