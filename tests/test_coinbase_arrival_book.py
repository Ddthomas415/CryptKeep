import json
import pytest
from scripts.research.observe_coinbase_arrival_book import capture, observe, URL


class Clock:
    now = 1_000_000_000
    def time_ns(self):
        return self.now
    def monotonic_ns(self):
        return self.now
    def sleep(self, seconds):
        self.now += int(seconds * 1_000_000_000)


class Session:
    def __init__(self, status=200, product="BTC-USD"):
        self.calls = []
        self.status = status
        self.product = product
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        payload = {"pricebook": {"product_id": self.product,
                   "bids": [{"price": "100", "size": "1"}],
                   "asks": [{"price": "101", "size": "1"}]}}
        class Response:
            status_code = self.status
            content = json.dumps(payload).encode()
            def json(self):
                return payload
        return Response()


def test_two_public_reads_preserve_unknown_alignment():
    import base64
    import hashlib
    session = Session()
    result = observe("BTC-USD", session, Clock())
    assert len(session.calls) == 2
    assert all(url == URL and kw["allow_redirects"] is False
               and kw["timeout"] == 15 for url, kw in session.calls)
    assert result["arrival"]["request_utc_ns"] == result["local_target_utc_ns"]
    assert result["arrival"]["arrival_alignment"] == "UNVERIFIED"
    assert result["scoring_authorized"] is False
    assert result["orders_submitted"] is False
    for row in (result["initial"], result["arrival"]):
        raw = base64.b64decode(row["raw_response_base64"], validate=True)
        assert hashlib.sha256(raw).hexdigest() == row["raw_sha256"]
        assert json.loads(raw) == row["raw_payload"]


@pytest.mark.parametrize("status,product", [(307, "BTC-USD"), (500, "BTC-USD"),
                                            (200, "ETH-USD")])
def test_failed_or_wrong_product_capture_is_not_qualified(status, product):
    with pytest.raises(ValueError):
        capture("BTC-USD", Session(status, product), Clock())


def test_unsupported_product_never_requests():
    session = Session()
    with pytest.raises(ValueError):
        capture("AI-USD", session, Clock())
    assert session.calls == []
