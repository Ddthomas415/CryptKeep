from __future__ import annotations

from domain.policy.decision import PolicyDecision, allow, deny
from domain.policy.reason_codes import MODE_BLOCKED
from shared.schemas.api import Mode, RiskStatus


def can_submit_new_order(*, mode: Mode, risk_state: RiskStatus) -> PolicyDecision:
    if mode == Mode.RESEARCH_ONLY:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[MODE_BLOCKED])
    return allow(mode=mode, risk_state=risk_state)


def mode_requires_approval(mode: Mode) -> bool:
    return mode == Mode.LIVE_APPROVAL

