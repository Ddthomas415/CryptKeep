from __future__ import annotations

from dataclasses import dataclass

from domain.policy.reason_codes import (
    FUTURES_APPROVAL_REQUIRED,
    LOW_CONFIDENCE_APPROVAL,
    NEW_ASSET_APPROVAL_REQUIRED,
    NEW_EXCHANGE_APPROVAL_REQUIRED,
    RISK_RESTRICTED_APPROVAL,
    TRADE_SIZE_ABOVE_THRESHOLD,
)
from shared.schemas.api import Mode, RiskStatus


@dataclass(frozen=True)
class TradeSpec:
    asset: str
    venue_type: str
    size_pct: float
    confidence: float
    is_new_asset: bool
    is_new_exchange: bool


@dataclass(frozen=True)
class ApprovalPolicyConfig:
    approval_size_threshold_pct: float = 1.0
    min_confidence: float = 0.65
    require_approval_for_futures: bool = True
    require_approval_for_low_confidence: bool = True
    require_approval_in_paper: bool = False


def evaluate_approval_requirement(
    *,
    mode: Mode,
    risk_state: RiskStatus,
    trade: TradeSpec,
    policy: ApprovalPolicyConfig,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if mode == Mode.LIVE_APPROVAL:
        reasons.append("MODE_REQUIRES_APPROVAL")
    if mode == Mode.PAPER and policy.require_approval_in_paper:
        reasons.append("PAPER_REQUIRES_APPROVAL")
    if float(trade.size_pct or 0.0) > float(policy.approval_size_threshold_pct or 0.0):
        reasons.append(TRADE_SIZE_ABOVE_THRESHOLD)
    if policy.require_approval_for_low_confidence and float(trade.confidence) < float(policy.min_confidence):
        reasons.append(LOW_CONFIDENCE_APPROVAL)
    if policy.require_approval_for_futures and str(trade.venue_type).lower() == "futures":
        reasons.append(FUTURES_APPROVAL_REQUIRED)
    if bool(trade.is_new_asset):
        reasons.append(NEW_ASSET_APPROVAL_REQUIRED)
    if bool(trade.is_new_exchange):
        reasons.append(NEW_EXCHANGE_APPROVAL_REQUIRED)
    if risk_state == RiskStatus.RESTRICTED:
        reasons.append(RISK_RESTRICTED_APPROVAL)

    return (len(reasons) > 0), reasons

