from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from backend.app.domain.state_machines.mode import Mode
from backend.app.domain.state_machines.safety import SafetyState


class ApprovalLevel(str, Enum):
    NONE = "none"
    SOFT = "soft_approval"
    HARD = "hard_approval"


class TradeFacts(BaseModel):
    venue_type: str
    size_pct: float
    confidence: float
    is_new_asset: bool = False
    is_new_exchange: bool = False


class ApprovalPolicyConfig(BaseModel):
    approval_size_threshold_pct: float = 2.0
    min_confidence: float = 0.65
    require_approval_for_futures: bool = True
    require_approval_for_low_confidence: bool = True


def evaluate_approval_requirement(
    *,
    mode: Mode,
    risk_state: SafetyState,
    trade: TradeFacts,
    policy: ApprovalPolicyConfig,
) -> tuple[ApprovalLevel, list[str]]:
    reason_codes: list[str] = []
    level = ApprovalLevel.NONE

    if mode == Mode.LIVE_APPROVAL:
        reason_codes.append("MODE_REQUIRES_APPROVAL")
        level = ApprovalLevel.HARD
    if trade.size_pct > policy.approval_size_threshold_pct:
        reason_codes.append("SIZE_ABOVE_THRESHOLD")
        level = ApprovalLevel.HARD
    if (
        policy.require_approval_for_low_confidence
        and trade.confidence < policy.min_confidence
    ):
        reason_codes.append("LOW_CONFIDENCE_APPROVAL_REQUIRED")
        level = ApprovalLevel.HARD
    if policy.require_approval_for_futures and trade.venue_type == "futures":
        reason_codes.append("FUTURES_APPROVAL_REQUIRED")
        level = ApprovalLevel.HARD
    if trade.is_new_asset:
        reason_codes.append("NEW_ASSET_APPROVAL_REQUIRED")
        level = ApprovalLevel.HARD
    if trade.is_new_exchange:
        reason_codes.append("NEW_EXCHANGE_APPROVAL_REQUIRED")
        level = ApprovalLevel.HARD
    if risk_state in {SafetyState.RESTRICTED, SafetyState.PAUSED, SafetyState.BLOCKED}:
        reason_codes.append("RISK_STATE_APPROVAL_REQUIRED")
        if level == ApprovalLevel.NONE:
            level = ApprovalLevel.SOFT

    return level, reason_codes
