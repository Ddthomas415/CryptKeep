from backend.app.domain.workflows.ask_research import execute_ask_research_workflow
from backend.app.domain.workflows.connect_exchange import execute_connect_exchange_workflow
from backend.app.domain.workflows.execute_terminal_command import execute_terminal_workflow
from backend.app.domain.workflows.switch_mode import execute_switch_mode_workflow
from backend.app.domain.workflows.update_risk_limits import execute_update_risk_limits_workflow


def test_ask_research_requires_question() -> None:
    result = execute_ask_research_workflow({"asset": "SOL"})
    assert result.success is False
    assert result.code == "QUESTION_REQUIRED"


def test_connect_exchange_returns_partial_success_for_read_only() -> None:
    result = execute_connect_exchange_workflow(
        {
            "provider": "coinbase",
            "label": "Coinbase Read",
            "credentials": {"api_key": "k", "api_secret": "s", "read_only": True},
        }
    )
    assert result.success is True
    assert result.state == "partial_success"


def test_switch_mode_blocks_live_auto_for_non_owner() -> None:
    result = execute_switch_mode_workflow(
        {
            "current_mode": "research_only",
            "target_mode": "live_auto",
            "role": "trader",
            "has_trade_connection": True,
            "risk_configured": True,
            "explicit_confirmation": True,
        }
    )
    assert result.success is False
    assert result.code == "ROLE_NOT_ALLOWED"


def test_terminal_workflow_owner_gets_confirmation_for_dangerous_command() -> None:
    result = execute_terminal_workflow(
        {
            "role": "owner",
            "mode": "research_only",
            "risk_state": "safe",
            "kill_switch_on": False,
            "command": "kill-switch on",
        }
    )
    assert result.success is True
    assert "Require user confirmation" in result.next_actions


def test_update_risk_limits_owner_success() -> None:
    result = execute_update_risk_limits_workflow(
        {
            "role": "owner",
            "workspace_id": "ws_1",
            "limits": {"max_daily_loss_pct": 5},
        }
    )
    assert result.success is True
    assert result.code == "RISK_LIMITS_UPDATED"
