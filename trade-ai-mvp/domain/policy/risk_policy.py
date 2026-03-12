from __future__ import annotations

from domain.policy.decision import PolicyDecision, allow, deny
from domain.policy.reason_codes import RISK_STATE_BLOCKED
from shared.schemas.api import Mode, RiskStatus


def evaluate_risk_state_for_action(
    *,
    mode: Mode,
    risk_state: RiskStatus,
    risk_increasing: bool,
) -> PolicyDecision:
    if risk_state == RiskStatus.BLOCKED and risk_increasing:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[RISK_STATE_BLOCKED])
    if risk_state == RiskStatus.PAUSED and risk_increasing:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[RISK_STATE_BLOCKED])
    return allow(mode=mode, risk_state=risk_state)

