from __future__ import annotations

import pytest

from services.execution.intent_lifecycle import (
    EXECUTION_STORE_STATUS_TRANSITIONS,
    LIVE_QUEUE_STATUS_TRANSITIONS,
    execution_store_transition_allowed,
)


_EXPECTED_EXECUTION_STORE = {
    "pending": {"submitted", "canceled", "error"},
    "submitted": {"filled", "canceled", "error", "partially_filled"},
    "partially_filled": {"filled", "canceled", "error"},
    "filled": set(),
    "canceled": set(),
    "error": set(),
}

_EXPECTED_EXECUTION_STORE_TERMINALS = {"filled", "canceled", "error"}


def test_execution_store_state_machine_content_is_pinned():
    assert EXECUTION_STORE_STATUS_TRANSITIONS == _EXPECTED_EXECUTION_STORE, (
        "the execution-store state machine changed. Downstream tests DERIVE from "
        "this map and will follow the change without failing. Confirm the change "
        "is intended and reviewed."
    )


def test_terminal_statuses_are_exactly_the_expected_set():
    terminals = {
        status
        for status, successors in EXECUTION_STORE_STATUS_TRANSITIONS.items()
        if not successors
    }

    assert terminals == _EXPECTED_EXECUTION_STORE_TERMINALS, (
        f"terminal intent statuses changed: {sorted(terminals)}; expected "
        f"{sorted(_EXPECTED_EXECUTION_STORE_TERMINALS)}"
    )


@pytest.mark.parametrize("terminal", sorted(_EXPECTED_EXECUTION_STORE_TERMINALS))
def test_no_transition_leaves_a_terminal_status(terminal: str):
    for target in sorted(_EXPECTED_EXECUTION_STORE):
        if target == terminal:
            continue
        assert execution_store_transition_allowed(terminal, target) is False


def test_same_status_transition_is_always_permitted():
    for status in sorted(EXECUTION_STORE_STATUS_TRANSITIONS):
        assert execution_store_transition_allowed(status, status) is True


def test_unmapped_status_permits_only_a_same_status_write():
    assert execution_store_transition_allowed("some_unknown_status", "some_unknown_status") is True
    assert execution_store_transition_allowed("some_unknown_status", "filled") is False


def test_live_queue_terminal_statuses_are_pinned():
    terminals = {
        status
        for status, successors in LIVE_QUEUE_STATUS_TRANSITIONS.items()
        if not successors
    }

    assert terminals == {"filled", "canceled", "cancelled", "rejected", "error", "expired"}, (
        f"the live-queue terminal set changed: {sorted(terminals)}. This store's "
        "SQL hardcodes its own transition predicate; verify both copies were "
        "updated deliberately."
    )
