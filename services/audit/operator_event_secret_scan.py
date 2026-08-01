from __future__ import annotations

from pathlib import Path
from typing import Any

from services.audit.jsonl_secret_scan import scan_jsonl_secret_fields
from services.audit.operator_event_journal import operator_event_journal_path


def scan_operator_event_journal(path: Path | None = None, *, require_events: bool = False) -> dict[str, Any]:
    src = Path(path) if path is not None else operator_event_journal_path()
    return scan_jsonl_secret_fields(
        src,
        require_events=require_events,
        missing_reason="operator_event_journal_missing",
        empty_reason="operator_event_journal_empty",
        json_reason="operator_event_json_unparseable",
    )
