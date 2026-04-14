from __future__ import annotations

from typing import Any

from services.market_data.local_data_reader import get_settings_view
from services.security.auth_runtime_guard import auth_runtime_guard_status


def get_deployment_mode() -> str:
    settings = get_settings_view() or {}
    security = settings.get("security", {})
    return str(security.get("auth_scope") or "local_private_only")


def get_deployment_truth() -> dict[str, Any]:
    status = auth_runtime_guard_status()
    return {
        "auth_scope": status.get("auth_scope"),
        "remote_access_hardened": status.get("remote_access_hardened"),
        "outer_access_control": status.get("outer_access_control"),
    }
