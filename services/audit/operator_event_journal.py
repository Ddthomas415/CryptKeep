from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir

REQUIRED_FIELDS = (
    "actor",
    "timestamp",
    "action",
    "target",
    "pre_state",
    "post_state",
    "result",
    "reason",
)

SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "auth",
    "bearer",
    "credential",
    "key",
    "password",
    "secret",
    "token",
)


class OperatorEventJournalError(RuntimeError):
    """Raised when an operator event cannot be validated or persisted."""


def operator_event_journal_path() -> Path:
    return data_dir() / "operator_events" / "operator_events.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean_text(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise OperatorEventJournalError(f"missing_required_field:{field}")
    return text


def _redact(value: Any, *, path: str = "") -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            lowered = key.lower()
            child_path = f"{path}.{key}" if path else key
            if any(part in lowered for part in SENSITIVE_KEY_PARTS):
                out[key] = "<redacted>"
            else:
                out[key] = _redact(raw_value, path=child_path)
        return out
    if isinstance(value, list):
        return [_redact(item, path=path) for item in value]
    return value


def build_operator_event(
    *,
    actor: Any,
    action: Any,
    target: Any,
    result: Any,
    reason: Any = "",
    pre_state: Any = None,
    post_state: Any = None,
    source: Any = "manual",
    extra: Any = None,
    timestamp: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    event = {
        "event_id": str(event_id or uuid.uuid4()),
        "actor": _clean_text(actor, field="actor"),
        "timestamp": str(timestamp or _utc_now()),
        "action": _clean_text(action, field="action"),
        "target": _clean_text(target, field="target"),
        "pre_state": _redact(pre_state if pre_state is not None else {}),
        "post_state": _redact(post_state if post_state is not None else {}),
        "result": _clean_text(result, field="result"),
        "reason": str(reason or ""),
        "source": str(source or "manual"),
        "extra": _redact(extra if extra is not None else {}),
    }
    missing = [field for field in REQUIRED_FIELDS if field not in event]
    if missing:
        raise OperatorEventJournalError(f"missing_required_fields:{','.join(missing)}")
    return event


def append_operator_event(
    *,
    actor: Any,
    action: Any,
    target: Any,
    result: Any,
    reason: Any = "",
    pre_state: Any = None,
    post_state: Any = None,
    source: Any = "manual",
    extra: Any = None,
    path: Path | None = None,
) -> dict[str, Any]:
    event = build_operator_event(
        actor=actor,
        action=action,
        target=target,
        result=result,
        reason=reason,
        pre_state=pre_state,
        post_state=post_state,
        source=source,
        extra=extra,
    )
    dest = Path(path) if path is not None else operator_event_journal_path()
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    except Exception as exc:
        raise OperatorEventJournalError(f"operator_event_write_failed:{type(exc).__name__}") from exc
    return {**event, "path": str(dest)}


def load_operator_events(path: Path | None = None, *, limit: int | None = None) -> list[dict[str, Any]]:
    src = Path(path) if path is not None else operator_event_journal_path()
    if not src.exists():
        return []
    rows: list[dict[str, Any]] = []
    with src.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if limit is not None and limit >= 0:
        return rows[-int(limit):]
    return rows

