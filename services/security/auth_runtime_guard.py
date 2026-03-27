from __future__ import annotations

import os
from typing import Any, Dict

try:
    from dashboard.services.view_data import get_settings_view
except Exception:  # pragma: no cover - dashboard settings are optional at runtime
    get_settings_view = None


def _truthy(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def auth_runtime_guard_status() -> Dict[str, Any]:
    app_env = str(os.getenv("APP_ENV", "")).strip().lower() or "unknown"
    bypass_requested = _truthy("BYPASS_DASHBOARD_AUTH")
    env_login_requested = _truthy("CBP_ALLOW_ENV_LOGIN")
    bootstrap_user_present = bool(str(os.getenv("CBP_AUTH_BOOTSTRAP_USER", "")).strip())
    bootstrap_password_present = bool(str(os.getenv("CBP_AUTH_BOOTSTRAP_PASSWORD", "")).strip())
    auth_scope = "local_private_only"
    outer_access_control = ""
    try:
        data = get_settings_view() or {} if callable(get_settings_view) else {}
        security = data.get("security") if isinstance(data.get("security"), dict) else {}
        auth_scope = str(security.get("auth_scope") or auth_scope).strip().lower() or auth_scope
        outer_access_control = str(security.get("outer_access_control") or "").strip().lower()
    except Exception:
        pass

    violations: list[str] = []
    warnings: list[str] = []

    if bypass_requested and app_env != "dev":
        violations.append("BYPASS_DASHBOARD_AUTH is set outside APP_ENV=dev")

    if env_login_requested and app_env != "dev":
        violations.append("CBP_ALLOW_ENV_LOGIN is set outside APP_ENV=dev")

    if bootstrap_user_present != bootstrap_password_present:
        warnings.append("Bootstrap auth env is partially configured")
    if auth_scope == "remote_public_candidate" and not outer_access_control:
        violations.append("Remote/public candidate mode is set without an outer access-control layer")

    return {
        "app_env": app_env,
        "bypass_requested": bypass_requested,
        "env_login_requested": env_login_requested,
        "bootstrap_user_present": bootstrap_user_present,
        "bootstrap_password_present": bootstrap_password_present,
        "auth_scope": auth_scope,
        "outer_access_control": outer_access_control,
        "violations": violations,
        "warnings": warnings,
        "ok": not violations,
    }
