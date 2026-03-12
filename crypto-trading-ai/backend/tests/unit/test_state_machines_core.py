from backend.app.domain.state_machines.approval import (
    ApprovalState,
    can_transition_approval,
)
from backend.app.domain.state_machines.kill_switch import (
    KillSwitchState,
    can_transition_kill_switch,
)
from backend.app.domain.state_machines.mode import Mode, can_transition_mode
from backend.app.domain.state_machines.order import OrderState, can_transition_order
from backend.app.domain.state_machines.position import PositionState, can_transition_position
from backend.app.domain.state_machines.recommendation import (
    RecommendationState,
    can_transition_recommendation,
)
from backend.app.domain.state_machines.safety import SafetyState, can_transition_safety


def test_mode_transition_to_live_requires_confirmation() -> None:
    result = can_transition_mode(
        Mode.RESEARCH_ONLY,
        Mode.LIVE_APPROVAL,
        context={"has_trade_connection": True, "risk_configured": True, "kill_switch_on": False},
    )
    assert result.allowed is False
    assert result.reason == "CONFIRMATION_REQUIRED"


def test_recommendation_ready_to_approved_requires_approval() -> None:
    denied = can_transition_recommendation(RecommendationState.READY, RecommendationState.APPROVED)
    assert denied.allowed is False

    allowed = can_transition_recommendation(
        RecommendationState.READY,
        RecommendationState.APPROVED,
        context={"approval_granted": True},
    )
    assert allowed.allowed is True


def test_approval_pending_to_approved_requires_allowed_actor() -> None:
    denied = can_transition_approval(ApprovalState.PENDING, ApprovalState.APPROVED)
    assert denied.allowed is False

    allowed = can_transition_approval(
        ApprovalState.PENDING,
        ApprovalState.APPROVED,
        context={"approver_allowed": True},
    )
    assert allowed.allowed is True


def test_order_rejected_vs_failed_actor_guards() -> None:
    rejected_bad = can_transition_order(
        OrderState.SUBMITTED,
        OrderState.REJECTED,
        context={"actor_type": "system"},
    )
    assert rejected_bad.allowed is False

    rejected_ok = can_transition_order(
        OrderState.SUBMITTED,
        OrderState.REJECTED,
        context={"actor_type": "exchange"},
    )
    assert rejected_ok.allowed is True


def test_position_closing_to_closed_requires_zero_exposure() -> None:
    denied = can_transition_position(PositionState.CLOSING, PositionState.CLOSED)
    assert denied.allowed is False

    allowed = can_transition_position(
        PositionState.CLOSING,
        PositionState.CLOSED,
        context={"net_size_zero": True},
    )
    assert allowed.allowed is True


def test_kill_switch_release_requires_checks() -> None:
    denied = can_transition_kill_switch(KillSwitchState.RELEASING, KillSwitchState.OFF)
    assert denied.allowed is False

    allowed = can_transition_kill_switch(
        KillSwitchState.RELEASING,
        KillSwitchState.OFF,
        context={"release_checks_passed": True},
    )
    assert allowed.allowed is True


def test_safety_downshift_requires_recovery_confirmation() -> None:
    denied = can_transition_safety(SafetyState.BLOCKED, SafetyState.RESTRICTED)
    assert denied.allowed is False

    allowed = can_transition_safety(
        SafetyState.BLOCKED,
        SafetyState.RESTRICTED,
        context={"recovery_confirmed": True},
    )
    assert allowed.allowed is True
