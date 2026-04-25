from __future__ import annotations

import pytest

from services.execution.state_authority import (
    LiveStateContext,
    LiveStateViolation,
    update_live_queue_status_as_reconciler,
)


class _FakeLiveQueue:
    def __init__(self) -> None:
        self.updates: list[tuple[str, str, str | None]] = []

    def update_status(self, intent_id: str, status: str, *, last_error: str | None = None) -> None:
        self.updates.append((intent_id, status, last_error))


def _reconciler_ctx() -> LiveStateContext:
    return LiveStateContext(authority="RECONCILER", origin="test")


def test_reconciler_live_queue_update_allows_submitted_to_error() -> None:
    qdb = _FakeLiveQueue()

    update_live_queue_status_as_reconciler(
        qdb,
        {"intent_id": "intent-1", "status": "submitted"},
        "error",
        ctx=_reconciler_ctx(),
        last_error="stale_order_not_found",
    )

    assert qdb.updates == [("intent-1", "error", "stale_order_not_found")]


@pytest.mark.parametrize("target", ["filled", "canceled", "rejected"])
def test_reconciler_live_queue_update_allows_submitted_terminal_targets(target: str) -> None:
    qdb = _FakeLiveQueue()

    update_live_queue_status_as_reconciler(
        qdb,
        {"intent_id": "intent-1", "status": "submitted"},
        target,
        ctx=_reconciler_ctx(),
        last_error=None,
    )

    assert qdb.updates == [("intent-1", target, None)]


def test_reconciler_live_queue_update_blocks_invalid_transition() -> None:
    qdb = _FakeLiveQueue()

    with pytest.raises(LiveStateViolation, match="invalid source"):
        update_live_queue_status_as_reconciler(
            qdb,
            {"intent_id": "intent-1", "status": "queued"},
            "error",
            ctx=_reconciler_ctx(),
            last_error="not_submitted",
        )

    assert qdb.updates == []


def test_reconciler_live_queue_update_blocks_terminal_overwrite() -> None:
    qdb = _FakeLiveQueue()

    with pytest.raises(LiveStateViolation, match="terminal status"):
        update_live_queue_status_as_reconciler(
            qdb,
            {"intent_id": "intent-1", "status": "filled"},
            "error",
            ctx=_reconciler_ctx(),
            last_error="late_error",
        )

    assert qdb.updates == []


@pytest.mark.parametrize(
    "ctx",
    [
        None,
        LiveStateContext(authority="UNKNOWN", origin="test"),
        LiveStateContext(authority="INTENT_CONSUMER", origin="test"),
    ],
)
def test_reconciler_live_queue_update_blocks_missing_or_wrong_authority(
    ctx: LiveStateContext | None,
) -> None:
    qdb = _FakeLiveQueue()

    with pytest.raises(LiveStateViolation):
        update_live_queue_status_as_reconciler(
            qdb,
            {"intent_id": "intent-1", "status": "submitted"},
            "rejected",
            ctx=ctx,
            last_error="reject",
        )

    assert qdb.updates == []
