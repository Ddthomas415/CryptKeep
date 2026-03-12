from __future__ import annotations

from backend.app.domain.state_machines.mode import Mode


MODE_ACTION_MATRIX: dict[Mode, set[str]] = {
    Mode.RESEARCH_ONLY: {
        "research_query",
        "generate_recommendation",
        "create_alert",
        "test_connection",
    },
    Mode.PAPER: {
        "research_query",
        "generate_recommendation",
        "create_alert",
        "test_connection",
        "submit_paper_order",
        "approve_paper_trade",
        "close_position",
        "cancel_order",
    },
    Mode.LIVE_APPROVAL: {
        "research_query",
        "generate_recommendation",
        "create_alert",
        "test_connection",
        "submit_live_order",
        "approve_live_trade",
        "close_position",
        "cancel_order",
    },
    Mode.LIVE_AUTO: {
        "research_query",
        "generate_recommendation",
        "create_alert",
        "test_connection",
        "submit_live_order",
        "close_position",
        "cancel_order",
        "auto_execute",
    },
}


def mode_allows_action(mode: Mode, action: str) -> bool:
    return action in MODE_ACTION_MATRIX.get(mode, set())
