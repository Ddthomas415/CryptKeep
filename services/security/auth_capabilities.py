from __future__ import annotations

import importlib
import os
from typing import Any

from services.security.auth_runtime_guard import auth_runtime_guard_status

_AUTH_SCOPE_LABELS = {
    "local_private_only": "Local/private only",
    "remote_public_candidate": "Remote/public candidate",
}


def _load_user_auth_store() -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module("services.security.user_auth_store"), None
    except Exception as exc:
        return None, f"user_auth_store unavailable: {type(exc).__name__}: {exc}"


def _keychain_available() -> tuple[bool, str | None]:
    mod, error = _load_user_auth_store()
    if mod is None:
        return False, error
    keychain_available = getattr(mod, "keychain_available", None)
    if not callable(keychain_available):
        return False, "user_auth_store unavailable: missing keychain_available"
    try:
        return keychain_available()
    except Exception as exc:
        return False, f"keychain_available failed: {type(exc).__name__}: {exc}"


def _env_login_available() -> bool:
    app_env = str(os.environ.get("APP_ENV", "")).strip().lower()
    explicit = str(os.environ.get("CBP_ALLOW_ENV_LOGIN", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    creds_present = bool(os.environ.get("CBP_AUTH_USERNAME") and os.environ.get("CBP_AUTH_PASSWORD"))
    return app_env == "dev" and explicit and creds_present


def _security_policy() -> dict[str, Any]:
    auth_scope = "local_private_only"
    remote_requires_mfa = True
    outer_access_control = ""
    try:
        from services.market_data.local_data_reader import get_settings_view

        data = get_settings_view() or {}
        security = data.get("security") if isinstance(data.get("security"), dict) else {}
        raw_scope = str(security.get("auth_scope") or auth_scope).strip().lower()
        if raw_scope in _AUTH_SCOPE_LABELS:
            auth_scope = raw_scope
        remote_requires_mfa = bool(security.get("remote_access_requires_mfa", True))
        outer_access_control = str(security.get("outer_access_control") or "").strip().lower()
    except Exception as _silent_err:
        _LOG.debug("suppressed: %s", _silent_err)

    scope_detail = (
        "Configured for local/private use. Remote/public exposure is not hardened by the app."
        if auth_scope == "local_private_only"
        else "Remote/public use requires an external MFA, VPN, or reverse-proxy access layer before exposure."
    )
    mfa_detail = "Built-in TOTP MFA is available for keychain-backed users."
    if remote_requires_mfa:
        mfa_detail += " Remote/public deployment still requires MFA plus stronger outer access controls."

    return {
        "auth_scope": auth_scope,
        "auth_scope_label": _AUTH_SCOPE_LABELS.get(auth_scope, _AUTH_SCOPE_LABELS["local_private_only"]),
        "remote_access_requires_mfa": remote_requires_mfa,
        "scope_detail": scope_detail,
        "mfa_detail": mfa_detail,
        "outer_access_control": outer_access_control,
    }


def auth_capabilities() -> dict[str, Any]:
    keychain_ok, detail = _keychain_available()
    env_fallback = _env_login_available()
    guard = auth_runtime_guard_status()
    policy = _security_policy()

    recommended = "os_keychain" if keychain_ok else ("env_credentials" if env_fallback else "unavailable")

    return {
        "local_role_selector": False,
        "os_keychain": keychain_ok,
        "env_credentials": env_fallback,
        "oauth": False,
        "sso": False,
        "recommended": recommended,
        "detail": detail,
        "auth_scope": str(policy.get("auth_scope") or "local_private_only"),
        "auth_scope_label": str(policy.get("auth_scope_label") or _AUTH_SCOPE_LABELS["local_private_only"]),
        "scope_detail": str(policy.get("scope_detail") or ""),
        "built_in_mfa": True,
        "remote_access_requires_mfa": bool(policy.get("remote_access_requires_mfa", True)),
        "outer_access_control": str(policy.get("outer_access_control") or ""),
        "remote_access_hardened": bool(
            str(policy.get("auth_scope") or "local_private_only") == "remote_public_candidate"
            and bool(policy.get("remote_access_requires_mfa", True))
            and bool(str(policy.get("outer_access_control") or "").strip())
        ),
        "mfa_detail": str(policy.get("mfa_detail") or ""),
        "runtime_guard_ok": bool(guard.get("ok")),
        "runtime_guard_violations": list(guard.get("violations") or []),
        "runtime_guard_warnings": list(guard.get("warnings") or []),
    }
