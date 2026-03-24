from services.execution.order_reconciliation import reconcile_ambiguous_submission


class DummyClient:
    def __init__(self, order=None, client_oid_order=None, fetch_raises=False, find_raises=False):
        self._order = order
        self._client_oid_order = client_oid_order
        self._fetch_raises = fetch_raises
        self._find_raises = find_raises

    def fetch_order(self, order_id: str, symbol: str):
        if self._fetch_raises:
            raise RuntimeError("fetch failed")
        return self._order

    def find_order_by_client_oid(self, symbol: str, client_oid: str):
        if self._find_raises:
            raise RuntimeError("find failed")
        return self._client_oid_order


def test_remote_order_id_confirms_placed():
    client = DummyClient(order={"id": "123"})
    out = reconcile_ambiguous_submission(
        venue="binance",
        client=client,
        symbol="BTC/USDT",
        client_oid="abc",
        remote_order_id="123",
        age_sec=0,
    )
    assert out.outcome == "confirmed_placed"


def test_client_oid_not_found_confirms_not_placed_for_safe_venue():
    client = DummyClient(client_oid_order=None)
    out = reconcile_ambiguous_submission(
        venue="binance",
        client=client,
        symbol="BTC/USDT",
        client_oid="abc",
        remote_order_id=None,
        age_sec=0,
    )
    assert out.outcome == "confirmed_not_placed"


def test_unknown_venue_is_inconclusive():
    client = DummyClient(client_oid_order=None)
    out = reconcile_ambiguous_submission(
        venue="unknown",
        client=client,
        symbol="BTC/USDT",
        client_oid="abc",
        remote_order_id=None,
        age_sec=0,
    )
    assert out.outcome == "inconclusive"


def test_client_oid_lookup_error_is_inconclusive():
    client = DummyClient(find_raises=True)
    out = reconcile_ambiguous_submission(
        venue="binance",
        client=client,
        symbol="BTC/USDT",
        client_oid="abc",
        remote_order_id=None,
        age_sec=0,
    )
    assert out.outcome == "inconclusive"
