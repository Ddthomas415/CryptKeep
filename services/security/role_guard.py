"""services/security/role_guard.py

Role-based access control helper.
Canonical location (moved from dashboard/role_guard.py).
"""
from __future__ import annotations
from typing import Literal

Role = Literal["viewer", "trader", "admin", "VIEWER", "OPERATOR", "ADMIN"]
_ROLE_RANK = {"viewer": 0, "trader": 1, "admin": 2}
_ROLE_ALIASES = {
    "viewer": "viewer",
    "trader": "trader",
    "admin": "admin",
    "operator": "trader",
    "VIEWER": "viewer",
    "OPERATOR": "trader",
    "ADMIN": "admin",
}


def _normalize_role(role: str) -> str:
    return _ROLE_ALIASES.get(str(role), str(role).lower())


def require_role(current: Role, required: Role) -> None:
    """Raise PermissionError if current role is below required."""
    current_norm = _normalize_role(current)
    required_norm = _normalize_role(required)
    if _ROLE_RANK.get(current_norm, -1) < _ROLE_RANK.get(required_norm, 999):
        raise PermissionError(
            f"Role '{current}' does not meet required '{required}'"
        )
