from __future__ import annotations

from typing import Any
import importlib


def _keychain_available() -> tuple[bool, str | None]:
    try:
        ss = importlib.import_module("services.security.secret_store")
    except Exception as e:
        return False, str(e)

    # Common availability probes, if present
    for name in ("available", "is_available", "keychain_available", "secret_store_available"):
        fn = getattr(ss, name, None)
        if callable(fn):
            try:
                return bool(fn()), None
            except Exception as e:
                return False, str(e)

    # Common class-based patterns, if present
    for name in ("SecretStore", "KeychainStore", "CredentialStore"):
        cls = getattr(ss, name, None)
        if cls is not None:
            try:
                obj = cls()
                avail = getattr(obj, "available", None)
                if callable(avail):
                    return bool(avail()), None
                return True, None
            except Exception as e:
                return False, str(e)

    # If the module exists but has no explicit probe, treat it as present but unknown
    return True, None


def auth_capabilities() -> dict[str, Any]:
    keychain_ok, detail = _keychain_available()

    return {
        "local_role_selector": True,
        "os_keychain": keychain_ok,
        "oauth": False,
        "sso": False,
        "recommended": "os_keychain" if keychain_ok else "local_role_selector",
        "detail": detail,
    }
