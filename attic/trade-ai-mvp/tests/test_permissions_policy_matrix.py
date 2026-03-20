from __future__ import annotations

from domain.policy import (
    ApprovalPolicyConfig,
    ConnectionPermission,
    Role,
    TradeIntent,
    TradePolicyContext,
    TradeSpec,
    VenueType,
    can_run_terminal_command,
    evaluate_trade_policy,
)
from domain.policy.reason_codes import (
    APPROVAL_REQUIRED,
    COMMAND_BLOCKED,
    FUTURES_NOT_SUPPORTED,
    KILL_SWITCH_ACTIVE,
    MODE_BLOCKED,
    ROLE_NOT_ALLOWED,
    TRADE_SIZE_ABOVE_THRESHOLD,
)
from shared.schemas.api import ConnectionStatus, Mode, RiskStatus


def _base_connection() -> ConnectionPermission:
    return ConnectionPermission(
        read_enabled=True,
        trade_enabled=True,
        spot_supported=True,
        futures_supported=True,
        sandbox_only=False,
        status=ConnectionStatus.CONNECTED,
    )


def _base_trade(**overrides) -> TradeSpec:
    base = dict(
        asset="SOL",
        venue_type=VenueType.SPOT.value,
        size_pct=0.5,
        confidence=0.9,
        is_new_asset=False,
        is_new_exchange=False,
    )
    base.update(overrides)
    return TradeSpec(**base)


def _base_policy(**overrides) -> ApprovalPolicyConfig:
    base = dict(
        approval_size_threshold_pct=1.0,
        min_confidence=0.65,
        require_approval_for_futures=True,
        require_approval_for_low_confidence=True,
        require_approval_in_paper=False,
    )
    base.update(overrides)
    return ApprovalPolicyConfig(**base)


def test_owner_live_auto_safe_trade_allowed_without_approval():
    ctx = TradePolicyContext(
        role=Role.OWNER,
        mode=Mode.LIVE_AUTO,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
        connection=_base_connection(),
        trade=_base_trade(),
        policy=_base_policy(),
        intent=TradeIntent.OPEN,
    )
    out = evaluate_trade_policy(ctx)
    assert out.allowed is True
    assert out.requires_approval is False
    assert out.reason_codes == []


def test_analyst_trade_submit_blocked_by_role():
    ctx = TradePolicyContext(
        role=Role.ANALYST,
        mode=Mode.PAPER,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
        connection=_base_connection(),
        trade=_base_trade(),
        policy=_base_policy(),
        intent=TradeIntent.OPEN,
    )
    out = evaluate_trade_policy(ctx)
    assert out.allowed is False
    assert ROLE_NOT_ALLOWED in out.reason_codes


def test_research_mode_blocks_new_order():
    ctx = TradePolicyContext(
        role=Role.TRADER,
        mode=Mode.RESEARCH_ONLY,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
        connection=_base_connection(),
        trade=_base_trade(),
        policy=_base_policy(),
        intent=TradeIntent.OPEN,
    )
    out = evaluate_trade_policy(ctx)
    assert out.allowed is False
    assert MODE_BLOCKED in out.reason_codes


def test_live_approval_requires_approval():
    ctx = TradePolicyContext(
        role=Role.TRADER,
        mode=Mode.LIVE_APPROVAL,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
        connection=_base_connection(),
        trade=_base_trade(),
        policy=_base_policy(),
        intent=TradeIntent.OPEN,
    )
    out = evaluate_trade_policy(ctx)
    assert out.allowed is True
    assert out.requires_approval is True
    assert APPROVAL_REQUIRED in out.reason_codes


def test_size_threshold_triggers_approval():
    ctx = TradePolicyContext(
        role=Role.TRADER,
        mode=Mode.LIVE_AUTO,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
        connection=_base_connection(),
        trade=_base_trade(size_pct=2.5),
        policy=_base_policy(approval_size_threshold_pct=1.0),
        intent=TradeIntent.OPEN,
    )
    out = evaluate_trade_policy(ctx)
    assert out.allowed is True
    assert out.requires_approval is True
    assert APPROVAL_REQUIRED in out.reason_codes
    assert TRADE_SIZE_ABOVE_THRESHOLD in out.reason_codes


def test_kill_switch_blocks_risk_increasing_but_allows_reduce():
    open_ctx = TradePolicyContext(
        role=Role.TRADER,
        mode=Mode.LIVE_AUTO,
        risk_state=RiskStatus.SAFE,
        kill_switch=True,
        connection=_base_connection(),
        trade=_base_trade(),
        policy=_base_policy(),
        intent=TradeIntent.OPEN,
    )
    out_open = evaluate_trade_policy(open_ctx)
    assert out_open.allowed is False
    assert KILL_SWITCH_ACTIVE in out_open.reason_codes

    reduce_ctx = TradePolicyContext(
        role=Role.TRADER,
        mode=Mode.LIVE_AUTO,
        risk_state=RiskStatus.SAFE,
        kill_switch=True,
        connection=_base_connection(),
        trade=_base_trade(),
        policy=_base_policy(),
        intent=TradeIntent.REDUCE,
    )
    out_reduce = evaluate_trade_policy(reduce_ctx)
    assert out_reduce.allowed is True


def test_futures_not_supported_blocks():
    conn = ConnectionPermission(
        read_enabled=True,
        trade_enabled=True,
        spot_supported=True,
        futures_supported=False,
        sandbox_only=False,
        status=ConnectionStatus.CONNECTED,
    )
    ctx = TradePolicyContext(
        role=Role.TRADER,
        mode=Mode.LIVE_AUTO,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
        connection=conn,
        trade=_base_trade(venue_type=VenueType.FUTURES.value),
        policy=_base_policy(),
        intent=TradeIntent.OPEN,
    )
    out = evaluate_trade_policy(ctx)
    assert out.allowed is False
    assert FUTURES_NOT_SUPPORTED in out.reason_codes


def test_terminal_permissions_for_read_and_dangerous_commands():
    read_out = can_run_terminal_command(
        role=Role.ANALYST,
        command="why sol",
        mode=Mode.RESEARCH_ONLY,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
    )
    assert read_out.allowed is True

    danger_out = can_run_terminal_command(
        role=Role.ANALYST,
        command="approve trade 124",
        mode=Mode.LIVE_APPROVAL,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
    )
    assert danger_out.allowed is False
    assert ROLE_NOT_ALLOWED in danger_out.reason_codes


def test_terminal_blocks_raw_shell_and_viewer_connection_test():
    shell_out = can_run_terminal_command(
        role=Role.OWNER,
        command="bash -lc ls",
        mode=Mode.RESEARCH_ONLY,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
    )
    assert shell_out.allowed is False
    assert COMMAND_BLOCKED in shell_out.reason_codes

    viewer_test = can_run_terminal_command(
        role=Role.VIEWER,
        command="connections test coinbase",
        mode=Mode.RESEARCH_ONLY,
        risk_state=RiskStatus.SAFE,
        kill_switch=False,
    )
    assert viewer_test.allowed is False
    assert ROLE_NOT_ALLOWED in viewer_test.reason_codes

