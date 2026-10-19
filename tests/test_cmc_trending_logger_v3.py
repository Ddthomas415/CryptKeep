import importlib.util
from pathlib import Path
import sys
import datetime as dt
import json

import pytest

FOLDER = Path(__file__).parents[1] / "docs/research/cmc_trending_log"
spec = importlib.util.spec_from_file_location("cmc_v3", FOLDER / "cmc_trending_logger_v3.py")
logger = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(FOLDER))
try:
    spec.loader.exec_module(logger)
finally:
    sys.path.pop(0)


def evidence():
    return {"mismatches": [{"cmc_id": i, "symbol": s, "venue": "coinbase"}
                           for i, s in ((40925, "AI"), (40780, "META"))]}


def test_verified_request_requires_certificate_and_hostname_checks(monkeypatch):
    import ssl
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self):
            return b'{"ok":true}'
    def open_request(req, *, timeout, context):
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is True
        assert timeout == 30
        return Response()
    monkeypatch.setattr(logger.urllib.request, "urlopen", open_request)
    result = logger.verified_request("https://example.com")
    assert result["payload"] == {"ok": True}
    assert result["response_sha256"]


def test_certificate_failure_is_preserved_without_retry(monkeypatch):
    import ssl
    calls = []
    def fail(*args, **kwargs):
        calls.append(1)
        raise ssl.SSLCertVerificationError("untrusted certificate")
    monkeypatch.setattr(logger.urllib.request, "urlopen", fail)
    result = logger.verified_request("https://example.com")
    assert result["payload"] is None
    assert "untrusted certificate" in result["error"]
    assert len(calls) == 1


def test_exact_collisions_override_operator_mapping_keep_quote():
    rows = [{"cmc_id": i, "coinbase_product": s + "-USD", "identity_status": "OPERATOR_MAPPED",
             "quote": {"raw": "preserved"}} for i, s in ((40925, "AI"), (40780, "META"))]
    result = logger.qualify({"tracked_coinbase": rows, "trending_hidden_boost": []}, evidence())
    assert all(r["identity_status"] == "KNOWN_MISMATCH" and not r["identity_eligible"] for r in rows)
    assert all(r["quote"] == {"raw": "preserved"} for r in rows)
    assert result["schema_version"] == 3


def test_unverified_cannot_score_and_no_ticker_wide_ban():
    rows = [{"cmc_id": 1, "coinbase_product": "AI-USD", "identity_status": "OPERATOR_MAPPED"},
            {"cmc_id": 2, "coinbase_product": "OGN-USD", "identity_status": "UNVERIFIED"}]
    logger.qualify({"tracked_coinbase": rows, "trending_hidden_boost": []}, evidence())
    assert rows[0]["identity_eligible"]
    assert not rows[1]["identity_eligible"]


def test_evidence_absent_fails_visibly():
    with pytest.raises(ValueError, match="evidence"):
        logger.qualify({"tracked_coinbase": [], "trending_hidden_boost": []}, {"mismatches": []})


def test_book_capture_deduplicates_preserves_raw_sizes_and_ticker():
    ticker = {"payload": {"bid": "10", "ask": "11"}}
    result = {"tracked_coinbase": [{"coinbase_product": "BTC-USD", "quote": ticker},
                                    {"coinbase_product": "BTC-USD", "quote": ticker}]}
    calls = []
    raw = {"payload": {"bids": [["10", "2", 3]], "asks": [["11", "4", 2]],
                       "sequence": 42, "auction_mode": True},
           "request_started_utc": "2026-10-09T10:00:00Z",
           "received_utc": "2026-10-09T10:00:01Z", "response_sha256": "rawhash"}
    def fetch(url):
        calls.append(url)
        return raw
    logger.capture_books(result, fetch)
    assert len(calls) == 2
    assert all(url.endswith("/book?level=1") for url in calls)
    assert result["coinbase_level1_books"]["BTC-USD"]["response"] == raw
    assert result["tracked_coinbase"][0]["quote"] == ticker
    assert result["coinbase_level1_books"]["BTC-USD"]["execution"] == "NOT_FILL_PROOF"


def test_book_failure_retained_without_losing_other_products():
    result = {"tracked_coinbase": [{"coinbase_product": "X-USD"}]}
    def fetch(url):
        if "/X-USD/" in url:
            raise TimeoutError("book unavailable")
        return {"payload": {"bids": [], "asks": []}}
    logger.capture_books(result, fetch)
    assert "book unavailable" in result["coinbase_level1_books"]["X-USD"]["response"]["error"]
    assert len(result["coinbase_level1_books"]) == 3


def test_collect_save_and_departed_cohort_replay(tmp_path):
    now = dt.datetime(2026, 10, 10, 14, tzinfo=dt.timezone.utc)
    calls = []

    def fetch(url, body=None):
        calls.append(url)
        if url == logger.base.CMC:
            payload = {"data": {"list": [{"type": "listing", "tokenSymbol": "AI", "cryptoId": 40925}]}}
        elif url.endswith("/products"):
            payload = [{"id": "AI-USD", "quote_currency": "USD", "status": "online"}]
        else:
            payload = {"bid": "1", "ask": "2"}
        return {"payload": payload, "received_utc": now.isoformat()}

    first = logger.collect(tmp_path, {"40925": {"coinbase_product": "AI-USD", "evidence": "operator"}},
                           fetch=fetch, now=now)
    assert first["tls_policy"] == "CUSTOM_TRANSPORT_UNVERIFIED"
    assert "ca_bundle_sha256" not in first
    path = logger.base.save(tmp_path, first)
    original = path.read_bytes()
    assert json.loads(original)["schema_version"] == 3
    assert not first["tracked_coinbase"][0]["identity_eligible"]
    assert first["trending_hidden_boost"][0]["identity_status"] == "KNOWN_MISMATCH"

    def departed(url, body=None):
        if url == logger.base.CMC:
            return {"payload": {"data": {"list": []}}}
        return fetch(url, body)

    second = logger.collect(tmp_path, fetch=departed, now=now + dt.timedelta(days=1))
    assert len(second["tracked_coinbase"]) == 1
    assert second["tracked_coinbase"][0]["identity_status"] == "KNOWN_MISMATCH"
    assert path.read_bytes() == original
    assert logger.base.CB + "/products/AI-USD/ticker" in calls
