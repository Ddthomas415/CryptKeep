from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from domain.policy.approval_policy import ApprovalPolicyConfig, TradeSpec, evaluate_approval_requirement
from domain.policy.connection_policy import ConnectionPermission, evaluate_connection_for_trade
from domain.policy.decision import PolicyDecision, allow, deny
from domain.policy.modes import can_submit_new_order
from domain.policy.reason_codes import APPROVAL_REQUIRED, KILL_SWITCH_ACTIVE, ROLE_NOT_ALLOWED
from domain.policy.risk_policy import evaluate_risk_state_for_action
from domain.policy.roles import Role
from shared.schemas.api import Mode, RiskStatus


class VenueType(StrEnum):
    SPOT = "spot"
    FUTURES = "futures"


class TradeIntent(StrEnum):
    OPEN = "open"
    INCREASE = "increase"
    REDUCE = "reduce"
    CLOSE = "close"


@dataclass(frozen=True)
class TradePolicyContext:
    role: Role
    mode: Mode
    risk_state: RiskStatus
    kill_switch: bool
    connection: ConnectionPermission
    trade: TradeSpec
    policy: ApprovalPolicyConfig
    intent: TradeIntent = TradeIntent.OPEN


def _is_risk_increasing(intent: TradeIntent) -> bool:
    return intent in {TradeIntent.OPEN, TradeIntent.INCREASE}


def evaluate_trade_policy(ctx: TradePolicyContext) -> PolicyDecision:
    risk_increasing = _is_risk_increasing(ctx.intent)

    # 1) role gate
    if ctx.role not in {Role.OWNER, Role.TRADER}:
        return deny(mode=ctx.mode, risk_state=ctx.risk_state, reason_codes=[ROLE_NOT_ALLOWED])

    # 2) mode gate
    mode_decision = can_submit_new_order(mode=ctx.mode, risk_state=ctx.risk_state)
    if not mode_decision.allowed and risk_increasing:
        return mode_decision

    # 3) kill switch gate
    if ctx.kill_switch and risk_increasing:
        return deny(mode=ctx.mode, risk_state=ctx.risk_state, reason_codes=[KILL_SWITCH_ACTIVE])

    # 4) risk-state gate
    risk_decision = evaluate_risk_state_for_action(
        mode=ctx.mode,
        risk_state=ctx.risk_state,
        risk_increasing=risk_increasing,
    )
    if not risk_decision.allowed:
        return risk_decision

    # 5) connection permissions
    conn_decision = evaluate_connection_for_trade(
        mode=ctx.mode,
        risk_state=ctx.risk_state,
        connection=ctx.connection,
        venue_type=ctx.trade.venue_type,
        risk_increasing=risk_increasing,
    )
    if not conn_decision.allowed:
        return conn_decision

    # 6) approval policy
    requires_approval, approval_codes = evaluate_approval_requirement(
        mode=ctx.mode,
        risk_state=ctx.risk_state,
        trade=ctx.trade,
        policy=ctx.policy,
    )
    if requires_approval:
        return allow(
            mode=ctx.mode,
            risk_state=ctx.risk_state,
            requires_approval=True,
            reason_codes=[APPROVAL_REQUIRED, *approval_codes],
        )

    return allow(mode=ctx.mode, risk_state=ctx.risk_state)

