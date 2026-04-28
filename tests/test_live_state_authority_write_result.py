from services.execution.state_authority import (
    LiveStateContext,
    update_live_queue_status_as_reconciler,
    update_live_queue_status_as_intent_consumer,
)


class RejectingQueue:
    def __init__(self):
        self.calls = []

    def update_status(self, intent_id, status, **kwargs):
        self.calls.append((intent_id, status, kwargs))
        return False


def test_reconciler_status_helper_returns_false_when_persistent_write_fails():
    qdb = RejectingQueue()
    ok = update_live_queue_status_as_reconciler(
        qdb,
        {"intent_id": "i1", "status": "submitted"},
        "filled",
        ctx=LiveStateContext(authority="RECONCILER", origin="test"),
    )

    assert ok is False
    assert qdb.calls == [("i1", "filled", {"last_error": None})]


def test_intent_consumer_status_helper_returns_false_when_persistent_write_fails():
    qdb = RejectingQueue()
    ok = update_live_queue_status_as_intent_consumer(
        qdb,
        {"intent_id": "i1", "status": "queued"},
        "submitted",
        ctx=LiveStateContext(authority="INTENT_CONSUMER", origin="test"),
        client_order_id="cid-1",
        exchange_order_id="ex-1",
    )

    assert ok is False
    assert qdb.calls == [
        (
            "i1",
            "submitted",
            {
                "last_error": None,
                "client_order_id": "cid-1",
                "exchange_order_id": "ex-1",
            },
        )
    ]
