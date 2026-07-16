from __future__ import annotations

import json
import logging
from typing import Any, Optional

from services.audit.operator_event_journal import append_operator_event

SERVICE_NAME = "crypto-bot-pro"  # keyring service namespace
_LOG = logging.getLogger(__name__)

def _require_keyring():
    try:
        import keyring  # type: ignore
        return keyring
    except Exception as e:
        raise RuntimeError("keyring_not_installed") from e

def _norm_exchange(x: str) -> str:
    return str(x).lower().strip()


def _stored_credential_summary(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {"present": False, "field_names": [], "parse_ok": True}
    try:
        obj = json.loads(raw)
    except Exception:
        return {"present": True, "field_names": [], "parse_ok": False}
    if not isinstance(obj, dict):
        return {"present": True, "field_names": [], "parse_ok": False}
    return {"present": True, "field_names": sorted(str(k) for k in obj.keys()), "parse_ok": True}


def _payload_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {"present": True, "field_names": sorted(str(k) for k in payload.keys()), "parse_ok": True}


def _record_credential_rotation_event(
    *,
    exchange: str,
    operation: str,
    result: str,
    reason: str,
    pre_state: dict[str, Any],
    post_state: dict[str, Any],
) -> dict[str, Any]:
    try:
        event = append_operator_event(
            actor="operator",
            action="api_credential_rotation",
            target=f"exchange:{exchange}",
            result=result,
            reason=reason,
            pre_state={"stored": pre_state},
            post_state={"stored": post_state},
            source="services.security.credential_store",
            extra={"surface": "credential_store", "operation": operation, "payload_values_logged": False},
        )
        return {"ok": True, "event_id": event.get("event_id"), "path": event.get("path")}
    except Exception as exc:
        _LOG.warning(
            "api_credential_rotation operator event journal failed: %s: %s",
            type(exc).__name__,
            exc,
        )
        return {"ok": False, "reason": f"operator_event_write_failed:{type(exc).__name__}"}


def set_exchange_credentials(exchange: str, api_key: str, api_secret: str, passphrase: str | None = None) -> dict:
    keyring = _require_keyring()
    ex = _norm_exchange(exchange)
    payload = {"apiKey": str(api_key).strip(), "secret": str(api_secret).strip()}
    if passphrase is not None and str(passphrase).strip():
        payload["passphrase"] = str(passphrase).strip()

    try:
        pre_state = _stored_credential_summary(keyring.get_password(SERVICE_NAME, ex))
    except Exception:
        pre_state = {"present": "unknown", "field_names": [], "parse_ok": False}
    keyring.set_password(SERVICE_NAME, ex, json.dumps(payload, sort_keys=True))
    operator_event = _record_credential_rotation_event(
        exchange=ex,
        operation="set_exchange_credentials",
        result="success",
        reason="set_exchange_credentials",
        pre_state=pre_state,
        post_state=_payload_summary(payload),
    )
    return {"ok": True, "exchange": ex, "fields": sorted(list(payload.keys())), "operator_event": operator_event}

def get_exchange_credentials(exchange: str) -> Optional[dict]:
    keyring = _require_keyring()
    ex = _norm_exchange(exchange)
    raw = keyring.get_password(SERVICE_NAME, ex)
    if not raw:
        return None
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and obj.get("apiKey") and obj.get("secret"):
            return obj
        return None
    except Exception:
        return None

def delete_exchange_credentials(exchange: str) -> dict:
    keyring = _require_keyring()
    ex = _norm_exchange(exchange)
    try:
        pre_state = _stored_credential_summary(keyring.get_password(SERVICE_NAME, ex))
    except Exception:
        pre_state = {"present": "unknown", "field_names": [], "parse_ok": False}
    try:
        keyring.delete_password(SERVICE_NAME, ex)
        deleted = True
    except Exception:
        # if it doesn't exist, treat as ok
        deleted = False
    post_state = (
        {"present": False, "field_names": [], "parse_ok": True}
        if deleted
        else {"present": "unknown", "field_names": [], "parse_ok": False}
    )
    operator_event = _record_credential_rotation_event(
        exchange=ex,
        operation="delete_exchange_credentials",
        result="success",
        reason=("delete_exchange_credentials:deleted" if deleted else "delete_exchange_credentials:not_deleted"),
        pre_state=pre_state,
        post_state=post_state,
    )
    return {"ok": True, "exchange": ex, "deleted": deleted, "operator_event": operator_event}

def credentials_status(exchange: str) -> dict:
    ex = _norm_exchange(exchange)
    creds = None
    try:
        creds = get_exchange_credentials(ex)
    except Exception as e:
        return {"ok": False, "exchange": ex, "present": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": True, "exchange": ex, "present": bool(creds), "fields": (sorted(list(creds.keys())) if creds else [])}
