from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    OWNER = "owner"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"


ROLE_ACTION_MATRIX: dict[str, set[Role]] = {
    "view_dashboard": {Role.OWNER, Role.TRADER, Role.ANALYST, Role.VIEWER},
    "view_connections": {Role.OWNER, Role.TRADER, Role.ANALYST, Role.VIEWER},
    "test_connection": {Role.OWNER, Role.TRADER, Role.ANALYST},
    "save_credentials": {Role.OWNER},
    "approve_paper_trade": {Role.OWNER, Role.TRADER},
    "approve_live_trade": {Role.OWNER, Role.TRADER},
    "reject_trade": {Role.OWNER, Role.TRADER},
    "edit_risk_limits": {Role.OWNER},
    "activate_kill_switch": {Role.OWNER, Role.TRADER},
    "deactivate_kill_switch": {Role.OWNER, Role.TRADER},
    "switch_mode_live_auto": {Role.OWNER},
    "terminal_read_only": {Role.OWNER, Role.TRADER, Role.ANALYST},
    "terminal_dangerous": {Role.OWNER, Role.TRADER},
}


def role_allows_action(role: Role, action: str) -> bool:
    allowed_roles = ROLE_ACTION_MATRIX.get(action)
    if not allowed_roles:
        return False
    return role in allowed_roles


def allowed_actions_for_role(role: Role) -> list[str]:
    actions: list[str] = []
    for action, roles in ROLE_ACTION_MATRIX.items():
        if role in roles:
            actions.append(action)
    return sorted(actions)
