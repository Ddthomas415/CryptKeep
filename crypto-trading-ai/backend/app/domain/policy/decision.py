from pydantic import BaseModel


class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool
    reason_codes: list[str]
    user_message: str
    effective_mode: str = "research_only"
    effective_risk_state: str = "safe"


def allow_policy(
    *,
    requires_approval: bool = False,
    reason_codes: list[str] | None = None,
    user_message: str = "Allowed.",
    effective_mode: str = "research_only",
    effective_risk_state: str = "safe",
) -> PolicyDecision:
    return PolicyDecision(
        allowed=True,
        requires_approval=requires_approval,
        reason_codes=reason_codes or [],
        user_message=user_message,
        effective_mode=effective_mode,
        effective_risk_state=effective_risk_state,
    )


def block_policy(
    *,
    reason_codes: list[str],
    user_message: str,
    effective_mode: str = "research_only",
    effective_risk_state: str = "safe",
) -> PolicyDecision:
    return PolicyDecision(
        allowed=False,
        requires_approval=False,
        reason_codes=reason_codes,
        user_message=user_message,
        effective_mode=effective_mode,
        effective_risk_state=effective_risk_state,
    )
