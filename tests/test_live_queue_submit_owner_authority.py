from services.execution.state_authority import (
    LiveStateContext,
    LiveStateViolation,
    update_live_queue_status_as_intent_consumer,
)


class FakeQDB:
    def __init__(self):
        self.calls = []

    def update_status(self, intent_id, status, **kwargs):
        self.calls.append((intent_id, status, kwargs))


def test_submit_owner_helper_allows_queued_to_submitted():
    qdb = FakeQDB()
    intent = {"intent_id": "i1", "status": "queued"}
    ctx = LiveStateContext(authority="INTENT_CONSUMER", origin="test")

    update_live_queue_status_as_intent_consumer(
        qdb, intent, "submitted", ctx=ctx, client_order_id="coid-1", exchange_order_id="oid-1"
    )

    assert qdb.calls == [
        ("i1", "submitted", {"last_error": None, "client_order_id": "coid-1", "exchange_order_id": "oid-1"})
    ]


def test_submit_owner_helper_blocks_wrong_authority():
    qdb = FakeQDB()
    intent = {"intent_id": "i1", "status": "queued"}
    ctx = LiveStateContext(authority="RECONCILER", origin="test")

    try:
        update_live_queue_status_as_intent_consumer(qdb, intent, "submitted", ctx=ctx)
    except LiveStateViolation as exc:
        assert "intent-consumer authority required" in str(exc)
    else:
        raise AssertionError("expected LiveStateViolation")


def test_submit_owner_helper_blocks_terminal_overwrite():
    qdb = FakeQDB()
    intent = {"intent_id": "i1", "status": "filled"}
    ctx = LiveStateContext(authority="INTENT_CONSUMER", origin="test")

    try:
        update_live_queue_status_as_intent_consumer(qdb, intent, "queued", ctx=ctx)
    except LiveStateViolation as exc:
        assert "terminal status" in str(exc)
    else:
        raise AssertionError("expected LiveStateViolation")
