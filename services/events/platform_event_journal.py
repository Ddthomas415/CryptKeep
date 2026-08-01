from __future__ import annotations

import json
import os
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.audit.operator_event_journal import SENSITIVE_KEY_PARTS
from services.os.app_paths import data_dir

SCHEMA_VERSION = "platform_event_v1"

SUPPORTED_EVENT_TYPES = (
    "CampaignStarted",
    "CampaignEnded",
    "StrategySignalProduced",
    "RiskDecisionMade",
    "EvidenceArtifactGenerated",
)


class PlatformEventJournalError(RuntimeError):
    """Raised when a platform event cannot be validated or persisted."""


def platform_event_journal_path() -> Path:
    return data_dir() / "platform_events" / "platform_events.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean_text(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise PlatformEventJournalError(f"missing_required_field:{field}")
    return text


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            if any(part in key.lower() for part in SENSITIVE_KEY_PARTS):
                out[key] = "<redacted>"
            else:
                out[key] = _redact(raw_value)
        return out
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _clean_optional(value: Any) -> str:
    return str(value or "").strip()


def build_platform_event(
    *,
    event_type: Any,
    producer: Any,
    payload: dict[str, Any] | None = None,
    source: Any = "manual",
    strategy_id: Any = "",
    strategy_version: Any = "",
    config_hash: Any = "",
    dataset_id: Any = "",
    evidence_artifact_id: Any = "",
    run_id: Any = "",
    commit_sha: Any = "",
    timestamp: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    cleaned_type = _clean_text(event_type, field="event_type")
    if cleaned_type not in SUPPORTED_EVENT_TYPES:
        raise PlatformEventJournalError(f"unsupported_event_type:{cleaned_type}")

    return {
        "schema_version": SCHEMA_VERSION,
        "event_id": str(event_id or uuid.uuid4()),
        "timestamp": str(timestamp or _utc_now()),
        "event_type": cleaned_type,
        "producer": _clean_text(producer, field="producer"),
        "source": _clean_text(source, field="source"),
        "commit_sha": _clean_optional(commit_sha) or os.getenv("CBP_COMMIT_SHA", "").strip() or "unknown",
        "provenance": {
            "strategy_id": _clean_optional(strategy_id),
            "strategy_version": _clean_optional(strategy_version),
            "config_hash": _clean_optional(config_hash),
            "dataset_id": _clean_optional(dataset_id),
            "evidence_artifact_id": _clean_optional(evidence_artifact_id),
            "run_id": _clean_optional(run_id),
        },
        "payload": _redact(payload or {}),
    }


def append_platform_event(
    *,
    event_type: Any,
    producer: Any,
    payload: dict[str, Any] | None = None,
    source: Any = "manual",
    strategy_id: Any = "",
    strategy_version: Any = "",
    config_hash: Any = "",
    dataset_id: Any = "",
    evidence_artifact_id: Any = "",
    run_id: Any = "",
    commit_sha: Any = "",
    path: Path | None = None,
) -> dict[str, Any]:
    event = build_platform_event(
        event_type=event_type,
        producer=producer,
        payload=payload,
        source=source,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        config_hash=config_hash,
        dataset_id=dataset_id,
        evidence_artifact_id=evidence_artifact_id,
        run_id=run_id,
        commit_sha=commit_sha,
    )
    dest = Path(path) if path is not None else platform_event_journal_path()
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    except Exception as exc:
        raise PlatformEventJournalError(f"platform_event_write_failed:{type(exc).__name__}") from exc
    return {**event, "path": str(dest)}


def load_platform_events(
    path: Path | None = None,
    *,
    limit: int | None = None,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    src = Path(path) if path is not None else platform_event_journal_path()
    if not src.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with src.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                text = line.strip()
                if not text:
                    continue
                row = json.loads(text)
                if not isinstance(row, dict):
                    raise PlatformEventJournalError(f"invalid_event_row:{line_no}")
                if event_type and row.get("event_type") != event_type:
                    continue
                rows.append(row)
    except PlatformEventJournalError:
        raise
    except Exception as exc:
        raise PlatformEventJournalError(f"platform_event_read_failed:{type(exc).__name__}") from exc
    if limit is not None and limit >= 0:
        return rows[-int(limit):]
    return rows


def summarize_platform_events(
    path: Path | None = None,
    *,
    event_type: str | None = None,
    require_events: bool = False,
) -> dict[str, Any]:
    src = Path(path) if path is not None else platform_event_journal_path()
    try:
        rows = load_platform_events(src, event_type=event_type)
    except PlatformEventJournalError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "path": str(src),
            "event_count": 0,
            "event_types": {},
            "producers": {},
        }
    if require_events and not rows:
        return {
            "ok": False,
            "reason": "platform_event_journal_empty",
            "path": str(src),
            "event_count": 0,
            "event_types": {},
            "producers": {},
        }
    type_counts = Counter(str(row.get("event_type", "")) for row in rows)
    producer_counts = Counter(str(row.get("producer", "")) for row in rows)
    return {
        "ok": True,
        "reason": "ok",
        "path": str(src),
        "event_count": len(rows),
        "event_types": dict(sorted(type_counts.items())),
        "producers": dict(sorted(producer_counts.items())),
        "latest": rows[-1] if rows else None,
    }

