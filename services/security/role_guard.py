"""services/security/role_guard.py

Role-based access control helper.
Canonical location (moved from dashboard/role_guard.py).
"""
from __future__ import annotations
from typing import Literal

Role = Literal["viewer", "trader", "admin"]
_ROLE_RANK = {"viewer": 0, "trader": 1, "admin": 2}


def require_role(current: Role, required: Role) -> None:
    """Raise PermissionError if current role is below required."""
    if _ROLE_RANK.get(current, -1) < _ROLE_RANK.get(required, 999):
        raise PermissionError(
            f"Role '{current}' does not meet required '{required}'"
        )
