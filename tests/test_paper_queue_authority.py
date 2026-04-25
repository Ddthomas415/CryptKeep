from services.execution.state_authority import LiveStateContext, paper_queue_status


class FakeQDB:
    def __init__(self):
        self.calls = []

    def update_status(self, intent_id, status, **kwargs):
        self.calls.append((intent_id, status, kwargs))


def test_paper_queue_status_passes_only_explicit_ids():
    qdb = FakeQDB()
    intent = {"intent_id": "i1", "status": "queued"}
    ctx = LiveStateContext(authority="INTENT_CONSUMER", origin="test")

    paper_queue_status(
        qdb,
        intent,
        "submitted",
        ctx=ctx,
        last_error=None,
        client_order_id="coid-1",
        linked_order_id="oid-1",
    )

    assert qdb.calls == [
        ("i1", "submitted", {"last_error": None, "client_order_id": "coid-1", "linked_order_id": "oid-1"})
    ]


def test_paper_queue_status_omits_missing_ids():
    qdb = FakeQDB()
    intent = {"intent_id": "i1", "status": "queued"}
    ctx = LiveStateContext(authority="RECONCILER", origin="test")

    paper_queue_status(
        qdb,
        intent,
        "rejected",
        ctx=ctx,
        last_error="boom",
    )

    assert qdb.calls == [
        ("i1", "rejected", {"last_error": "boom"})
    ]
