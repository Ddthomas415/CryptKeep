from __future__ import annotations

from typing import Any, Dict, Iterable

from services.evidence.ingest import ingest_event


def process_payload(
    payload: Dict[str, Any],
    *,
    source_id: str | None = None,
    source_type: str | None = "webhook",
    display_name: str | None = "Webhook Source",
    consent_confirmed: bool | None = True,
) -> Dict[str, Any]:
    return ingest_event(
        dict(payload or {}),
        source_id=source_id,
        source_type=source_type,
        display_name=display_name,
        consent_confirmed=consent_confirmed,
    )


def process_batch(
    payloads: Iterable[Dict[str, Any]],
    *,
    source_id: str | None = None,
    source_type: str | None = "webhook",
    display_name: str | None = "Webhook Source",
    consent_confirmed: bool | None = True,
) -> Dict[str, Any]:
    accepted = 0
    quarantined = 0
    errors = 0
    results: list[Dict[str, Any]] = []
    for payload in payloads:
        try:
            out = process_payload(
                payload,
                source_id=source_id,
                source_type=source_type,
                display_name=display_name,
                consent_confirmed=consent_confirmed,
            )
            results.append(out)
            if out.get("ok"):
                accepted += 1
            elif out.get("quarantined"):
                quarantined += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            results.append({"ok": False, "error": f"{type(e).__name__}: {e}"})
    return {
        "ok": True,
        "count": len(results),
        "accepted": accepted,
        "quarantined": quarantined,
        "errors": errors,
        "results": results,
    }
