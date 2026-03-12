from __future__ import annotations

from domain.state_machines import (
    ApprovalState,
    KillSwitchState,
    ModeState,
    OrderState,
    PositionState,
    RecommendationState,
    SafetyState,
    build_transition_audit_event,
    can_transition_approval,
    can_transition_kill_switch,
    can_transition_mode,
    can_transition_order,
    can_transition_position,
    can_transition_recommendation,
    can_transition_safety,
)
from shared.schemas.api import Mode


def test_mode_state_machine_guards():
    denied = can_transition_mode(
        from_state=ModeState.RESEARCH_ONLY,
        to_state=ModeState.LIVE_APPROVAL,
        has_trading_connection=False,
        risk_limits_configured=False,
        user_confirmed=False,
    )
    assert denied.allowed is False
    assert denied.reason == "MISSING_TRADING_CONNECTION"

    allowed = can_transition_mode(
        from_state=ModeState.RESEARCH_ONLY,
        to_state=ModeState.LIVE_AUTO,
        has_trading_connection=True,
        risk_limits_configured=True,
        user_confirmed=True,
        second_confirmation=True,
        kill_switch_available=True,
    )
    assert allowed.allowed is False  # direct transition not allowed
    assert allowed.reason == "TRANSITION_NOT_ALLOWED"

    allowed_step = can_transition_mode(
        from_state=ModeState.LIVE_APPROVAL,
        to_state=ModeState.LIVE_AUTO,
        has_trading_connection=True,
        risk_limits_configured=True,
        user_confirmed=True,
        second_confirmation=True,
        kill_switch_available=True,
    )
    assert allowed_step.allowed is True


def test_recommendation_state_machine_guards():
    blocked = can_transition_recommendation(
        from_state=RecommendationState.READY,
        to_state=RecommendationState.APPROVED,
        mode=Mode.PAPER,
        kill_switch=True,
    )
    assert blocked.allowed is False
    assert blocked.reason == "KILL_SWITCH_ACTIVE"

    allowed = can_transition_recommendation(
        from_state=RecommendationState.APPROVED,
        to_state=RecommendationState.CONVERTED_TO_ORDER,
        mode=Mode.LIVE_APPROVAL,
        kill_switch=False,
        risk_passed=True,
    )
    assert allowed.allowed is True


def test_approval_state_machine_guards():
    denied = can_transition_approval(
        from_state=ApprovalState.PENDING,
        to_state=ApprovalState.APPROVED,
        actor_authorized=False,
    )
    assert denied.allowed is False
    assert denied.reason == "ROLE_NOT_ALLOWED"

    allowed = can_transition_approval(
        from_state=ApprovalState.PENDING,
        to_state=ApprovalState.REJECTED,
    )
    assert allowed.allowed is True


def test_order_state_machine_rejected_vs_failed_split():
    rejected = can_transition_order(
        from_state=OrderState.SUBMITTED,
        to_state=OrderState.REJECTED,
        mode=Mode.PAPER,
    )
    failed = can_transition_order(
        from_state=OrderState.SUBMITTED,
        to_state=OrderState.FAILED,
        mode=Mode.PAPER,
    )
    assert rejected.allowed is True
    assert failed.allowed is True
    assert rejected.reason != failed.reason


def test_order_state_machine_kill_switch_override():
    blocked = can_transition_order(
        from_state=OrderState.CREATED,
        to_state=OrderState.SUBMITTED,
        mode=Mode.LIVE_AUTO,
        kill_switch=True,
    )
    assert blocked.allowed is False
    assert blocked.reason == "KILL_SWITCH_ACTIVE"


def test_position_state_machine_error_state_requires_reconciliation_issue():
    denied = can_transition_position(
        from_state=PositionState.OPEN,
        to_state=PositionState.ERROR_STATE,
        reconciliation_issue=False,
    )
    assert denied.allowed is False
    assert denied.reason == "ERROR_STATE_REQUIRES_RECONCILIATION_ISSUE"

    allowed = can_transition_position(
        from_state=PositionState.OPEN,
        to_state=PositionState.ERROR_STATE,
        reconciliation_issue=True,
    )
    assert allowed.allowed is True
    assert "trigger_position_reconciliation" in allowed.side_effects


def test_kill_switch_state_machine_transitions():
    arming = can_transition_kill_switch(
        from_state=KillSwitchState.OFF,
        to_state=KillSwitchState.ARMING,
        actor_authorized=True,
    )
    assert arming.allowed is True

    denied = can_transition_kill_switch(
        from_state=KillSwitchState.RELEASING,
        to_state=KillSwitchState.OFF,
        release_validated=False,
    )
    assert denied.allowed is False
    assert denied.reason == "RELEASE_VALIDATION_FAILED"


def test_safety_state_machine_kill_switch_forces_blocked():
    denied = can_transition_safety(
        from_state=SafetyState.WARNING,
        to_state=SafetyState.SAFE,
        kill_switch_on=True,
    )
    assert denied.allowed is False
    assert denied.reason == "KILL_SWITCH_FORCES_BLOCKED"

    escalated = can_transition_safety(
        from_state=SafetyState.WARNING,
        to_state=SafetyState.BLOCKED,
        kill_switch_on=True,
    )
    assert escalated.allowed is True


def test_transition_audit_builder_payload():
    transition = can_transition_order(
        from_state=OrderState.CREATED,
        to_state=OrderState.SUBMITTED,
        mode=Mode.PAPER,
        kill_switch=False,
    )
    event = build_transition_audit_event(
        entity_type="order",
        entity_id="ord_1",
        transition=transition,
        actor_type="user",
        actor_id="owner_1",
        request_id="req_1",
        context={"venue": "paper"},
    )
    assert event["entity_type"] == "order"
    assert event["previous_state"] == "created"
    assert event["next_state"] == "submitted"
    assert event["allowed"] is True
