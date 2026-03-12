from __future__ import annotations

from dataclasses import dataclass, field

from shared.schemas.api import Mode, RiskStatus

from domain.policy.reason_codes import message_for_codes


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason_codes: list[str] = field(default_factory=list)
    user_message: str = ""
    effective_mode: Mode = Mode.RESEARCH_ONLY
    effective_risk_state: RiskStatus = RiskStatus.SAFE


def allow(
    *,
    mode: Mode,
    risk_state: RiskStatus,
    requires_approval: bool = False,
    reason_codes: list[str] | None = None,
) -> PolicyDecision:
    codes = list(reason_codes or [])
    return PolicyDecision(
        allowed=True,
        requires_approval=bool(requires_approval),
        reason_codes=codes,
        user_message=message_for_codes(codes),
        effective_mode=mode,
        effective_risk_state=risk_state,
    )


def deny(*, mode: Mode, risk_state: RiskStatus, reason_codes: list[str]) -> PolicyDecision:
    codes = list(reason_codes)
    return PolicyDecision(
        allowed=False,
        requires_approval=False,
        reason_codes=codes,
        user_message=message_for_codes(codes),
        effective_mode=mode,
        effective_risk_state=risk_state,
    )

