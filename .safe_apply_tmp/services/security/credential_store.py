from __future__ import annotations

import json
from typing import Any, Dict, Optional

SERVICE_NAME = "crypto-bot-pro"  # keyring service namespace

def _require_keyring():
    try:
        import keyring  # type: ignore
        return keyring
    except Exception as e:
        raise RuntimeError("keyring_not_installed") from e

def _norm_exchange(x: str) -> str:
    return str(x).lower().strip()

def set_exchange_credentials(exchange: str, api_key: str, api_secret: str, passphrase: str | None = None) -> dict:
    keyring = _require_keyring()
    ex = _norm_exchange(exchange)
    payload = {"apiKey": str(api_key).strip(), "secret": str(api_secret).strip()}
    if passphrase is not None and str(passphrase).strip():
        payload["passphrase"] = str(passphrase).strip()

    keyring.set_password(SERVICE_NAME, ex, json.dumps(payload, sort_keys=True))
    return {"ok": True, "exchange": ex, "fields": sorted(list(payload.keys()))}

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
        keyring.delete_password(SERVICE_NAME, ex)
        return {"ok": True, "exchange": ex, "deleted": True}
    except Exception:
        # if it doesn't exist, treat as ok
        return {"ok": True, "exchange": ex, "deleted": False}

def credentials_status(exchange: str) -> dict:
    ex = _norm_exchange(exchange)
    creds = None
    try:
        creds = get_exchange_credentials(ex)
    except Exception as e:
        return {"ok": False, "exchange": ex, "present": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": True, "exchange": ex, "present": bool(creds), "fields": (sorted(list(creds.keys())) if creds else [])}
