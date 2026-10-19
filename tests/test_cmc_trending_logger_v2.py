import datetime as dt
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "docs/research/cmc_trending_log/cmc_trending_logger_v2.py"
SPEC = importlib.util.spec_from_file_location("cmc_v2", PATH)
logger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(logger)
NOW = dt.datetime(2026, 10, 10, 14, tzinfo=dt.timezone.utc)


def seed(directory, age=1):
    item = {"snapshot_utc": (NOW - dt.timedelta(days=age)).isoformat(),
            "trending_hidden_boost": [{"type": "listing", "symbol": "ABC", "cmc_id": 7,
                                       "coinbase": {"bid": "1", "ask": "2"}}]}
    path = directory / "legacy.json"
    path.write_text(json.dumps(item))
    return path.read_bytes()


def fetcher(rows=None, failure=False):
    calls = []

    def fetch(url, body=None):
        calls.append(url)
        envelope = {"received_utc": NOW.isoformat(), "request_started_utc": NOW.isoformat()}
        if url == logger.CMC:
            payload = {"data": {"list": rows or []}}
        elif url.endswith("/products"):
            payload = [{"id": "ABC-USD", "quote_currency": "USD", "status": "online"}]
        elif failure and "ABC-USD" in url:
            return {**envelope, "payload": None, "error": "unavailable"}
        else:
            payload = {"bid": "1", "ask": "2", "time": NOW.isoformat()}
        return {**envelope, "payload": payload}

    return fetch, calls


def test_departed_coin_retained_when_cmc_empty(tmp_path):
    before = seed(tmp_path)
    fetch, calls = fetcher()
    result = logger.collect(tmp_path, fetch=fetch, now=NOW)
    assert logger.CB + "/products/ABC-USD/ticker" in calls
    assert result["trending_status"] == "MISSING"
    assert result["tracked_coinbase"][0]["identity_status"] == "UNVERIFIED"
    assert (tmp_path / "legacy.json").read_bytes() == before


@pytest.mark.parametrize("age,expected", [(30, 1), (35, 1), (36, 0)])
def test_retention_boundary(tmp_path, age, expected):
    seed(tmp_path, age)
    fetch, _ = fetcher()
    assert len(logger.collect(tmp_path, fetch=fetch, now=NOW)["tracked_coinbase"]) == expected


def test_failed_quote_kept_not_dropped(tmp_path):
    seed(tmp_path)
    fetch, _ = fetcher(failure=True)
    row = logger.collect(tmp_path, fetch=fetch, now=NOW)["tracked_coinbase"][0]
    assert row["quote"]["quote_status"] == "MISSING"
    assert row["quote"]["error"] == "unavailable"


def test_mapping_requires_matching_product_and_evidence(tmp_path):
    seed(tmp_path)
    fetch, _ = fetcher()
    for identity, expected in [({}, "UNVERIFIED"),
                               ({"coinbase_product": "ABC-USD"}, "UNVERIFIED"),
                               ({"coinbase_product": "XYZ-USD", "evidence": "reviewed"}, "UNVERIFIED"),
                               ({"coinbase_product": "ABC-USD", "evidence": "reviewed"}, "OPERATOR_MAPPED")]:
        result = logger.collect(tmp_path, {"7": identity}, fetch=fetch, now=NOW)
        assert result["tracked_coinbase"][0]["identity_status"] == expected


def test_same_time_saves_are_distinct_and_history_readable(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "utcnow", lambda: NOW)
    fetch, _ = fetcher()
    result = logger.collect(tmp_path, fetch=fetch, now=NOW)
    first = logger.save(tmp_path, result)
    before = first.read_bytes()
    second = logger.save(tmp_path, result)
    assert first != second
    assert first.read_bytes() == before
    assert len(logger.read_history(tmp_path, NOW)) == 2


def test_corrupt_history_fails_visibly(tmp_path):
    (tmp_path / "bad.json").write_text("{bad")
    with pytest.raises(json.JSONDecodeError):
        logger.collect(tmp_path, now=NOW)


@pytest.mark.parametrize("bid,ask", [("nan", "2"), ("2", "1"), ("0", "1"), ("1", "inf")])
def test_invalid_quotes_are_missing(bid, ask):
    result = logger.quote(lambda url: {"payload": {"bid": bid, "ask": ask}}, "ABC-USD")
    assert result["quote_status"] == "MISSING"


def test_new_coin_remains_trackable_after_leaving(tmp_path):
    rows = [{"type": "listing", "cryptoId": 7, "tokenSymbol": "ABC"}]
    fetch, _ = fetcher(rows)
    first = logger.collect(tmp_path, fetch=fetch, now=NOW)
    logger.save(tmp_path, first)
    fetch, calls = fetcher()
    second = logger.collect(tmp_path, fetch=fetch, now=NOW + dt.timedelta(days=7))
    assert len(second["tracked_coinbase"]) == 1
    assert any("ABC-USD/ticker" in url for url in calls)


@pytest.mark.parametrize("payload", [{"data": "bad"}, {"data": {"list": [None]}},
                                      {"data": {"list": [{"tokenSymbol": None}]}}])
def test_malformed_cmc_does_not_stop_retained_capture(tmp_path, payload):
    seed(tmp_path)
    base, calls = fetcher()

    def malformed(url, body=None):
        result = base(url, body)
        if url == logger.CMC:
            result["payload"] = payload
        return result

    result = logger.collect(tmp_path, fetch=malformed, now=NOW)
    assert result["trending_status"] == "DEGRADED"
    assert result["source_errors"]
    assert result["tracked_coinbase"][0]["quote"]["quote_status"] == "OBSERVED_NOT_FILL_PROOF"
    assert any("ABC-USD/ticker" in url for url in calls)
def test_cleanup_denied_does_not_turn_published_snapshot_into_failure(tmp_path, monkeypatch):
    def denied(path):
        raise PermissionError("sandbox denies unlink")

    monkeypatch.setattr(logger.os, "unlink", denied)
    with pytest.warns(RuntimeWarning, match="cleanup denied"):
        target = logger.save(tmp_path, {"test": True})
    assert json.loads(target.read_text()) == {"test": True}
    assert len(list(tmp_path.glob(".pending_*"))) == 1


def test_cleanup_denied_preserves_publication_error(tmp_path, monkeypatch):
    def denied(path):
        raise PermissionError("sandbox denies unlink")

    def failed(source, target):
        raise OSError("publication failed")

    monkeypatch.setattr(logger.os, "unlink", denied)
    monkeypatch.setattr(logger.os, "link", failed)
    with pytest.warns(RuntimeWarning, match="cleanup denied"):
        with pytest.raises(OSError, match="publication failed"):
            logger.save(tmp_path, {"test": True})
    assert not list(tmp_path.glob("*.json"))
