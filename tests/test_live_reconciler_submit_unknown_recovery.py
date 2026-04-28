from services.execution.live_reconciler import _recover_submit_unknown_by_client_order_id


class FakeQueue:
    def __init__(self):
        self.calls = []

    def update_status(self, intent_id, status, **kwargs):
        self.calls.append((intent_id, status, kwargs))
        return True


class FakeLiveTrading:
    def __init__(self):
        self.orders = []

    def upsert_order(self, row):
        self.orders.append(dict(row))


class FakeAdapter:
    def __init__(self, recovered):
        self.recovered = recovered
        self.calls = []

    def find_order_by_client_oid(self, symbol, client_order_id):
        self.calls.append((symbol, client_order_id))
        return self.recovered


def _intent(**overrides):
    row = {
        "intent_id": "i1",
        "status": "submit_unknown",
        "client_order_id": "cid-1",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 1.0,
        "limit_price": 100.0,
    }
    row.update(overrides)
    return row


def test_submit_unknown_recovery_promotes_to_submitted():
    qdb = FakeQueue()
    ldb = FakeLiveTrading()
    ad = FakeAdapter({"id": "ex-1"})

    assert _recover_submit_unknown_by_client_order_id(
        qdb=qdb,
        ldb=ldb,
        ad=ad,
        intent=_intent(),
        venue="coinbase",
        symbol="BTC/USD",
    )

    assert ad.calls == [("BTC/USD", "cid-1")]
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
    assert ldb.orders[0]["client_order_id"] == "cid-1"
    assert ldb.orders[0]["exchange_order_id"] == "ex-1"
    assert ldb.orders[0]["status"] == "submitted"


def test_submit_unknown_recovery_noops_without_client_order_id():
    qdb = FakeQueue()
    ldb = FakeLiveTrading()
    ad = FakeAdapter({"id": "ex-1"})

    assert not _recover_submit_unknown_by_client_order_id(
        qdb=qdb,
        ldb=ldb,
        ad=ad,
        intent=_intent(client_order_id=""),
        venue="coinbase",
        symbol="BTC/USD",
    )

    assert ad.calls == []
    assert qdb.calls == []
    assert ldb.orders == []


def test_submit_unknown_recovery_noops_when_order_not_found():
    qdb = FakeQueue()
    ldb = FakeLiveTrading()
    ad = FakeAdapter(None)

    assert not _recover_submit_unknown_by_client_order_id(
        qdb=qdb,
        ldb=ldb,
        ad=ad,
        intent=_intent(),
        venue="coinbase",
        symbol="BTC/USD",
    )

    assert ad.calls == [("BTC/USD", "cid-1")]
    assert qdb.calls == []
    assert ldb.orders == []


def test_submit_unknown_recovery_does_not_write_order_when_queue_update_fails():
    qdb = FakeQueue()
    qdb.update_status = lambda *args, **kwargs: False
    ldb = FakeLiveTrading()
    ad = FakeAdapter({"id": "ex-1"})

    assert not _recover_submit_unknown_by_client_order_id(
        qdb=qdb,
        ldb=ldb,
        ad=ad,
        intent=_intent(),
        venue="coinbase",
        symbol="BTC/USD",
    )

    assert ad.calls == [("BTC/USD", "cid-1")]
    assert ldb.orders == []
