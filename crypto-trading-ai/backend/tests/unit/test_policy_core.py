from backend.app.domain.policy.approval_policy import (
    ApprovalLevel,
    ApprovalPolicyConfig,
    TradeFacts,
    evaluate_approval_requirement,
)
from backend.app.domain.policy.connection_policy import (
    ConnectionPolicyContext,
    can_submit_order,
)
from backend.app.domain.policy.modes import mode_allows_action
from backend.app.domain.policy.roles import Role, role_allows_action
from backend.app.domain.policy.risk_policy import risk_allows_action
from backend.app.domain.policy.terminal_policy import evaluate_terminal_command
from backend.app.domain.state_machines.mode import Mode
from backend.app.domain.state_machines.safety import SafetyState


def test_role_matrix_blocks_analyst_live_approval() -> None:
    assert role_allows_action(Role.ANALYST, "approve_live_trade") is False
    assert role_allows_action(Role.TRADER, "approve_live_trade") is True


def test_mode_matrix_blocks_live_submit_in_research_only() -> None:
    assert mode_allows_action(Mode.RESEARCH_ONLY, "submit_live_order") is False
    assert mode_allows_action(Mode.LIVE_APPROVAL, "submit_live_order") is True


def test_risk_policy_allows_risk_reducing_action_under_kill_switch() -> None:
    blocked, reason = risk_allows_action(
        SafetyState.BLOCKED,
        "submit_live_order",
        kill_switch_on=True,
    )
    assert blocked is False
    assert reason == "KILL_SWITCH_ACTIVE"

    allowed, reason = risk_allows_action(
        SafetyState.BLOCKED,
        "close_position",
        kill_switch_on=True,
    )
    assert allowed is True
    assert reason is None


def test_connection_policy_rejects_sandbox_live_trade() -> None:
    allowed, reasons = can_submit_order(
        ConnectionPolicyContext(
            read_enabled=True,
            trade_enabled=True,
            spot_supported=True,
            futures_supported=False,
            sandbox_only=True,
            status="connected",
        ),
        venue_type="spot",
        is_live=True,
    )
    assert allowed is False
    assert "SANDBOX_ONLY_CONNECTION" in reasons


def test_approval_policy_marks_hard_for_large_trade() -> None:
    level, reasons = evaluate_approval_requirement(
        mode=Mode.LIVE_AUTO,
        risk_state=SafetyState.SAFE,
        trade=TradeFacts(venue_type="spot", size_pct=5.0, confidence=0.9),
        policy=ApprovalPolicyConfig(approval_size_threshold_pct=2.0),
    )
    assert level == ApprovalLevel.HARD
    assert "SIZE_ABOVE_THRESHOLD" in reasons


def test_terminal_policy_requires_confirmation_for_dangerous_commands() -> None:
    denied = evaluate_terminal_command(
        role=Role.ANALYST,
        command="kill-switch on",
        mode=Mode.RESEARCH_ONLY,
        risk_state=SafetyState.SAFE,
        kill_switch_on=False,
    )
    assert denied.allowed is False

    allowed = evaluate_terminal_command(
        role=Role.OWNER,
        command="kill-switch on",
        mode=Mode.RESEARCH_ONLY,
        risk_state=SafetyState.SAFE,
        kill_switch_on=False,
    )
    assert allowed.allowed is True
    assert allowed.requires_approval is True
