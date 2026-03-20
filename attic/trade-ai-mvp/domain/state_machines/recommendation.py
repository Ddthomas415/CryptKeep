from __future__ import annotations

from enum import StrEnum

from domain.state_machines.common import TransitionResult, allow_transition, deny_transition
from shared.schemas.api import Mode


class RecommendationState(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED_TO_ORDER = "converted_to_order"
    CANCELLED = "cancelled"


_RECOMMENDATION_TRANSITIONS: dict[RecommendationState, set[RecommendationState]] = {
    RecommendationState.DRAFT: {RecommendationState.READY},
    RecommendationState.READY: {
        RecommendationState.PENDING_REVIEW,
        RecommendationState.APPROVED,
        RecommendationState.REJECTED,
        RecommendationState.EXPIRED,
        RecommendationState.CANCELLED,
    },
    RecommendationState.PENDING_REVIEW: {
        RecommendationState.APPROVED,
        RecommendationState.REJECTED,
        RecommendationState.EXPIRED,
        RecommendationState.CANCELLED,
    },
    RecommendationState.APPROVED: {RecommendationState.CONVERTED_TO_ORDER, RecommendationState.CANCELLED},
    RecommendationState.REJECTED: set(),
    RecommendationState.EXPIRED: set(),
    RecommendationState.CONVERTED_TO_ORDER: set(),
    RecommendationState.CANCELLED: set(),
}


def can_transition_recommendation(
    *,
    from_state: RecommendationState,
    to_state: RecommendationState,
    mode: Mode,
    risk_passed: bool = True,
    kill_switch: bool = False,
    recommendation_fresh: bool = True,
    market_drift_ok: bool = True,
) -> TransitionResult[RecommendationState]:
    if from_state == to_state:
        return allow_transition(from_state=from_state, to_state=to_state, reason="NO_OP")
    if to_state not in _RECOMMENDATION_TRANSITIONS.get(from_state, set()):
        return deny_transition(from_state=from_state, to_state=to_state, reason="TRANSITION_NOT_ALLOWED")

    if from_state in {RecommendationState.READY, RecommendationState.PENDING_REVIEW} and to_state == RecommendationState.APPROVED:
        if mode == Mode.RESEARCH_ONLY:
            return deny_transition(from_state=from_state, to_state=to_state, reason="MODE_BLOCKED")
        if kill_switch:
            return deny_transition(from_state=from_state, to_state=to_state, reason="KILL_SWITCH_ACTIVE")
        if not risk_passed:
            return deny_transition(from_state=from_state, to_state=to_state, reason="RISK_BLOCKED")
        if not recommendation_fresh:
            return deny_transition(from_state=from_state, to_state=to_state, reason="RECOMMENDATION_STALE")

    if from_state == RecommendationState.APPROVED and to_state == RecommendationState.CONVERTED_TO_ORDER:
        if mode not in {Mode.PAPER, Mode.LIVE_APPROVAL, Mode.LIVE_AUTO}:
            return deny_transition(from_state=from_state, to_state=to_state, reason="MODE_BLOCKED")
        if kill_switch:
            return deny_transition(from_state=from_state, to_state=to_state, reason="KILL_SWITCH_ACTIVE")
        if not risk_passed:
            return deny_transition(from_state=from_state, to_state=to_state, reason="RISK_BLOCKED")

    if to_state == RecommendationState.EXPIRED:
        if recommendation_fresh and market_drift_ok:
            return deny_transition(from_state=from_state, to_state=to_state, reason="NOT_EXPIRED")

    return allow_transition(from_state=from_state, to_state=to_state, reason="ALLOWED")
