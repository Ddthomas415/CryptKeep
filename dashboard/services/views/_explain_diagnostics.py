"""Opt-in explanation diagnostics. Never retain request secrets or response prose."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import re


_EVENTS: ContextVar[list | None] = ContextVar("explain_diagnostics", default=None)
_FIELDS = ("current_cause", "past_precedent", "future_catalyst", "evidence",
           "assistant_status", "execution_disabled")
_PROVIDERS = {"backend_api", "phase1_copilot", "dashboard_fallback", "openai", "fallback", "missing", "other"}
_OUTCOMES = {"missing_service_token", "json_received", "http_error", "timeout",
             "network_error", "invalid_json", "invalid_envelope", "missing_explanation_fields",
             "foreign_asset", "accepted", "static_fallback"}


def _provider(value):
    if value is None or value == "":
        return "missing"
    return value if isinstance(value, str) and value in _PROVIDERS else "other"


def response_summary(payload):
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(data, dict):
        return {"shape": "non_object"}
    status = data.get("assistant_status")
    evidence = data.get("evidence")
    citations = []
    for row in evidence[:16] if isinstance(evidence, list) else []:
        if not isinstance(row, dict):
            continue
        hashes = {}
        for key in ("document_id", "id", "url"):
            value = row.get(key)
            if key == "document_id" and type(value) is int and value > 0:
                value = str(value)
            if isinstance(value, str) and value:
                # JSON may contain escaped lone surrogates; observing them must not break the client.
                hashes[key + "_sha256"] = hashlib.sha256(value.encode("utf-8", errors="surrogatepass")).hexdigest()
        if hashes:
            citations.append(hashes)
    return {"shape": "object", "fields_present": [k for k in _FIELDS if k in data],
            "provider": _provider(status.get("provider") if isinstance(status, dict) else None),
            "execution_disabled": data.get("execution_disabled") if type(data.get("execution_disabled")) is bool else None,
            "evidence_count": len(evidence) if isinstance(evidence, list) else None,
            "citation_hashes": citations}


def sanitize_events(events):
    """Revalidate child-process diagnostics before copying them into a verifier receipt."""
    result = []
    for event in events[:16] if isinstance(events, list) else []:
        if not isinstance(event, dict):
            continue
        safe = {"route": event.get("route") if event.get("route") in ("primary", "companion", "dashboard") else "other",
                "stage": event.get("stage") if event.get("stage") in ("transport", "normalization", "selection") else "other",
                "outcome": event.get("outcome") if isinstance(event.get("outcome"), str) and event["outcome"] in _OUTCOMES else "other"}
        code = event.get("http_status")
        safe["http_status"] = code if type(code) is int and 100 <= code <= 599 else None
        summary = event.get("response")
        if isinstance(summary, dict):
            count = summary.get("evidence_count")
            fields = summary.get("fields_present")
            safe["response"] = {
                "shape": "object" if summary.get("shape") == "object" else "non_object",
                "fields_present": [k for k in _FIELDS if k in fields] if isinstance(fields, list) else [],
                "provider": _provider(summary.get("provider")),
                "execution_disabled": summary.get("execution_disabled") if type(summary.get("execution_disabled")) is bool else None,
                "evidence_count": count if type(count) is int and count >= 0 else None,
                "citation_hashes": []}
            rows = summary.get("citation_hashes")
            for row in rows[:16] if isinstance(rows, list) else []:
                if isinstance(row, dict):
                    safe["response"]["citation_hashes"].append({
                        k: v for k, v in row.items() if k in ("document_id_sha256", "id_sha256", "url_sha256")
                        and isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)})
        result.append(safe)
    return result


@contextmanager
def capture_explain_diagnostics():
    events = []
    token = _EVENTS.set(events)
    try:
        yield events
    finally:
        _EVENTS.reset(token)


def record_explain_event(route, stage, outcome, *, http_status=None, payload=None):
    events = _EVENTS.get()
    if events is not None and len(events) < 16:
        event = {"route": route, "stage": stage, "outcome": outcome, "http_status": http_status}
        if payload is not None:
            event["response"] = response_summary(payload)
        events.extend(sanitize_events([event]))
