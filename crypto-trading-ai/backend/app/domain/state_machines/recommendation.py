from __future__ import annotations

from enum import Enum

from backend.app.domain.state_machines.common import TransitionResult, allow_transition, block_transition


class RecommendationState(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED_TO_ORDER = "converted_to_order"
    CANCELLED = "cancelled"


ALLOWED_RECOMMENDATION_TRANSITIONS: set[tuple[RecommendationState, RecommendationState]] = {
    (RecommendationState.DRAFT, RecommendationState.READY),
    (RecommendationState.READY, RecommendationState.PENDING_REVIEW),
    (RecommendationState.READY, RecommendationState.APPROVED),
    (RecommendationState.READY, RecommendationState.REJECTED),
    (RecommendationState.READY, RecommendationState.EXPIRED),
    (RecommendationState.PENDING_REVIEW, RecommendationState.APPROVED),
    (RecommendationState.PENDING_REVIEW, RecommendationState.REJECTED),
    (RecommendationState.PENDING_REVIEW, RecommendationState.EXPIRED),
    (RecommendationState.APPROVED, RecommendationState.CONVERTED_TO_ORDER),
    (RecommendationState.APPROVED, RecommendationState.CANCELLED),
}


def can_transition_recommendation(
    from_state: RecommendationState,
    to_state: RecommendationState,
    *,
    context: dict | None = None,
) -> TransitionResult:
    if from_state == to_state:
        return allow_transition(from_state.value, to_state.value, reason="no_op")

    if (from_state, to_state) not in ALLOWED_RECOMMENDATION_TRANSITIONS:
        return block_transition(
            from_state.value, to_state.value, "RECOMMENDATION_TRANSITION_NOT_ALLOWED"
        )

    ctx = context or {}
    if to_state == RecommendationState.PENDING_REVIEW and not ctx.get("requires_approval", False):
        return block_transition(
            from_state.value,
            to_state.value,
            "APPROVAL_NOT_REQUIRED_FOR_PENDING_REVIEW",
        )
    if to_state == RecommendationState.APPROVED and not (
        ctx.get("approval_granted", False) or ctx.get("auto_approved", False)
    ):
        return block_transition(from_state.value, to_state.value, "APPROVAL_REQUIRED")
    if to_state == RecommendationState.CONVERTED_TO_ORDER and not ctx.get("order_created", False):
        return block_transition(from_state.value, to_state.value, "ORDER_NOT_CREATED")
    if to_state == RecommendationState.EXPIRED and not ctx.get("expired", True):
        return block_transition(from_state.value, to_state.value, "RECOMMENDATION_NOT_EXPIRED")

    side_effects: tuple[str, ...] = ()
    if to_state == RecommendationState.PENDING_REVIEW:
        side_effects = ("create_approval_record",)
    elif to_state == RecommendationState.CONVERTED_TO_ORDER:
        side_effects = ("link_order_and_recommendation",)

    return allow_transition(from_state.value, to_state.value, side_effects=side_effects)
