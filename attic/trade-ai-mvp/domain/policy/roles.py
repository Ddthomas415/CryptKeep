from __future__ import annotations

from enum import StrEnum

from domain.policy.decision import PolicyDecision, allow, deny
from domain.policy.reason_codes import ROLE_NOT_ALLOWED
from shared.schemas.api import Mode, RiskStatus


class Role(StrEnum):
    OWNER = "owner"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"


class RoleAction(StrEnum):
    VIEW_CONNECTIONS = "connections.view"
    MANAGE_CONNECTIONS = "connections.manage"
    TEST_CONNECTIONS = "connections.test"
    MANAGE_CREDENTIALS = "connections.credentials.manage"
    APPROVE_PAPER_TRADE = "trading.paper.approve"
    APPROVE_LIVE_TRADE = "trading.live.approve"
    REJECT_TRADE = "trading.reject"
    CANCEL_ORDER = "trading.order.cancel"
    CLOSE_POSITION = "trading.position.close"
    ENABLE_STRATEGY = "trading.strategy.enable"
    EDIT_RISK = "risk.edit"
    ACTIVATE_KILL_SWITCH = "risk.kill_switch.on"
    DEACTIVATE_KILL_SWITCH = "risk.kill_switch.off"
    ASK_RESEARCH = "research.ask"
    SAVE_EXPLANATION = "research.save"
    CREATE_ALERT = "alerts.create"
    EXPORT_AUDIT = "audit.export"
    MODE_SET_LIVE_AUTO = "mode.set.live_auto"


_ROLE_ACTIONS: dict[Role, set[RoleAction]] = {
    Role.OWNER: set(RoleAction),
    Role.TRADER: {
        RoleAction.VIEW_CONNECTIONS,
        RoleAction.TEST_CONNECTIONS,
        RoleAction.APPROVE_PAPER_TRADE,
        RoleAction.APPROVE_LIVE_TRADE,
        RoleAction.REJECT_TRADE,
        RoleAction.CANCEL_ORDER,
        RoleAction.CLOSE_POSITION,
        RoleAction.ENABLE_STRATEGY,
        RoleAction.ACTIVATE_KILL_SWITCH,
        RoleAction.DEACTIVATE_KILL_SWITCH,
        RoleAction.ASK_RESEARCH,
        RoleAction.SAVE_EXPLANATION,
        RoleAction.CREATE_ALERT,
    },
    Role.ANALYST: {
        RoleAction.VIEW_CONNECTIONS,
        RoleAction.TEST_CONNECTIONS,
        RoleAction.ASK_RESEARCH,
        RoleAction.SAVE_EXPLANATION,
        RoleAction.CREATE_ALERT,
    },
    Role.VIEWER: {
        RoleAction.VIEW_CONNECTIONS,
        RoleAction.ASK_RESEARCH,
    },
}


def can_role_perform(
    *,
    role: Role,
    action: RoleAction,
    mode: Mode = Mode.RESEARCH_ONLY,
    risk_state: RiskStatus = RiskStatus.SAFE,
) -> PolicyDecision:
    if action in _ROLE_ACTIONS.get(role, set()):
        return allow(mode=mode, risk_state=risk_state)
    return deny(mode=mode, risk_state=risk_state, reason_codes=[ROLE_NOT_ALLOWED])


def can_manage_credentials(role: Role) -> bool:
    return role == Role.OWNER

