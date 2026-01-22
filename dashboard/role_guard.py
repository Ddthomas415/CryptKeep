from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal["VIEWER", "OPERATOR", "ADMIN"]

ROLE_RANK = {"VIEWER": 0, "OPERATOR": 1, "ADMIN": 2}

def has_role(current: Role, required: Role) -> bool:
    return ROLE_RANK.get(str(current), 0) >= ROLE_RANK.get(str(required), 0)

def require_role(current: Role, required: Role) -> None:
    if not has_role(current, required):
        raise PermissionError(f"Requires role {required}, current role is {current}")

@dataclass(frozen=True)
class RolePolicy:
    generate_required: Role = "OPERATOR"
    approve_required: Role = "OPERATOR"
    execute_required: Role = "ADMIN"
