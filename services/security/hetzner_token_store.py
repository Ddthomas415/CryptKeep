from __future__ import annotations

from typing import Any

SERVICE_NAME = "crypto-bot-pro"
ACCOUNT_NAME = "hetzner_cloud:readonly"


def _require_keyring() -> Any:
    try:
        import keyring  # type: ignore
    except Exception as exc:
        raise RuntimeError("keyring_not_installed") from exc
    return keyring


def get_hetzner_api_token() -> str | None:
    raw = _require_keyring().get_password(SERVICE_NAME, ACCOUNT_NAME)
    token = str(raw or "").strip()
    return token or None


def set_hetzner_api_token(token: str) -> dict[str, object]:
    value = str(token or "").strip()
    if not value:
        return {"ok": False, "reason": "empty_token"}
    try:
        _require_keyring().set_password(SERVICE_NAME, ACCOUNT_NAME, value)
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"keyring_write_failed:{type(exc).__name__}",
        }
    return {"ok": True, "stored_in": "os_keyring", "account": ACCOUNT_NAME}


def delete_hetzner_api_token() -> dict[str, object]:
    try:
        keyring = _require_keyring()
        if get_hetzner_api_token() is None:
            return {
                "ok": True,
                "deleted": False,
                "stored_in": "os_keyring",
                "account": ACCOUNT_NAME,
            }
        keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
    except Exception as exc:
        return {
            "ok": False,
            "deleted": False,
            "reason": f"keyring_delete_failed:{type(exc).__name__}",
        }
    return {
        "ok": True,
        "deleted": True,
        "stored_in": "os_keyring",
        "account": ACCOUNT_NAME,
    }


def hetzner_api_token_status() -> dict[str, object]:
    try:
        present = get_hetzner_api_token() is not None
    except Exception as exc:
        return {
            "ok": False,
            "present": False,
            "reason": f"keyring_unavailable:{type(exc).__name__}",
        }
    return {
        "ok": True,
        "present": present,
        "stored_in": "os_keyring",
        "account": ACCOUNT_NAME,
    }
