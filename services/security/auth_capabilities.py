from __future__ import annotations

import os
from typing import Any

from services.security.user_auth_store import keychain_available


def _keychain_available() -> tuple[bool, str | None]:
    return keychain_available()


def auth_capabilities() -> dict[str, Any]:
    keychain_ok, detail = _keychain_available()
    env_fallback = bool(os.environ.get("CBP_AUTH_USERNAME") and os.environ.get("CBP_AUTH_PASSWORD"))
    recommended = "os_keychain" if keychain_ok else ("env_credentials" if env_fallback else "unavailable")

    return {
        "local_role_selector": False,
        "os_keychain": keychain_ok,
        "env_credentials": env_fallback,
        "oauth": False,
        "sso": False,
        "recommended": recommended,
        "detail": detail,
    }
