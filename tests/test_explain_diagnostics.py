"""Offline diagnostics and characterization of the unchanged explanation guard."""
import hashlib
import json
from types import SimpleNamespace
import urllib.error

import pytest

from dashboard.services.views import _explain_diagnostics as diag
from dashboard.services.views import _shared_http as http
from dashboard.services.views import _shared_signals as signals
from dashboard.services.views import market_view


SECRET = "never-include-this-fixture-token"


def payload(text="BTC demand increased."):
    return {"current_cause": text, "execution_disabled": True,
            "assistant_status": {"provider": "phase1_copilot", "message": SECRET},
            "evidence": [{"document_id": "fixture-doc", "url": "https://source.test/article?token=" + SECRET}]}


def client(monkeypatch, primary=None, companion=None):
    stub = SimpleNamespace(
        _default_explain_payload=lambda *args: {"assistant_status": {"provider": "dashboard_fallback"},
                                               "execution_disabled": True},
        _explain_mentions_foreign_asset=signals._explain_mentions_foreign_asset,
        _request_envelope=lambda *args, **kwargs: primary,
        _request_envelope_from_base=lambda *args, **kwargs: companion,
        _read_mock_envelope=lambda *args: None, PHASE1_ORCHESTRATOR_URL="http://fixture.invalid")
    monkeypatch.setattr(market_view, "_view_data", lambda: stub)


def test_receipt_reports_foreign_asset_rejection_and_static_fallback(monkeypatch):
    client(monkeypatch, companion=payload("SOL demand increased. " + SECRET))
    with diag.capture_explain_diagnostics() as events:
        result = market_view.get_research_explain("BTC", SECRET)
    assert result["assistant_status"]["provider"] == "dashboard_fallback"
    rejected = next(e for e in events if e["outcome"] == "foreign_asset")
    assert rejected["route"] == "companion"
    assert rejected["response"]["provider"] == "phase1_copilot"
    assert rejected["response"]["citation_hashes"][0]["document_id_sha256"] == hashlib.sha256(b"fixture-doc").hexdigest()
    assert events[-1]["outcome"] == "static_fallback"
    assert SECRET not in json.dumps(events)
    assert "source.test" not in json.dumps(events)


@pytest.mark.parametrize("route", ["primary", "companion"])
def test_guard_accepts_ordinary_words_through_actual_client(monkeypatch, route):
    source = payload("BTC context is unavailable; whether liquidity improves is unknown.")
    assert signals._explain_mentions_foreign_asset(source, "BTC") is False
    client(monkeypatch, primary=source if route == "primary" else None,
           companion=source if route == "companion" else None)
    with diag.capture_explain_diagnostics() as events:
        result = market_view.get_research_explain("BTC")
    assert result["current_cause"] == source["current_cause"]
    assert result["assistant_status"]["provider"] == "phase1_copilot"
    assert events[-1]["route"] == route and events[-1]["outcome"] == "accepted"
    assert not any(e["outcome"] in ("foreign_asset", "static_fallback") for e in events)


def test_valid_companion_response_and_guard_acceptance_are_unchanged(monkeypatch):
    source = payload()
    assert signals._explain_mentions_foreign_asset(source, "BTC") is False
    client(monkeypatch, companion=source)
    without_capture = market_view.get_research_explain("BTC")
    with diag.capture_explain_diagnostics() as events:
        result = market_view.get_research_explain("BTC")
    assert result == without_capture
    assert events[-1]["outcome"] == "accepted"
    assert events[-1]["route"] == "companion"
    assert not any(e["outcome"] == "static_fallback" for e in events)


def test_escaped_lone_surrogate_citation_does_not_change_client_behavior(monkeypatch):
    source = payload()
    source["evidence"] = json.loads('[{"document_id":"\\ud800","url":"https://source.test/\\udfff"}]')
    client(monkeypatch, primary=source)
    without_capture = market_view.get_research_explain("BTC")
    with diag.capture_explain_diagnostics() as events:
        result = market_view.get_research_explain("BTC")
    assert result == without_capture
    assert events[-1]["outcome"] == "accepted"
    digest = events[-1]["response"]["citation_hashes"][0]["document_id_sha256"]
    assert digest == hashlib.sha256("\ud800".encode("utf-8", errors="surrogatepass")).hexdigest()
    assert json.dumps(events).encode("utf-8")


@pytest.mark.parametrize("source,reason", [(None, "invalid_envelope"), ({"message": SECRET}, "missing_explanation_fields")])
def test_normalization_failures_have_specific_safe_reasons(monkeypatch, source, reason):
    client(monkeypatch, companion=source)
    with diag.capture_explain_diagnostics() as events:
        market_view.get_research_explain("BTC")
    assert any(e["route"] == "companion" and e["outcome"] == reason for e in events)
    assert SECRET not in json.dumps(events)


@pytest.mark.parametrize("failure,reason,status", [
    (urllib.error.HTTPError("https://secret.test/" + SECRET, 401, SECRET, {}, None), "http_error", 401),
    (TimeoutError(SECRET), "timeout", None),
    (urllib.error.URLError(SECRET), "network_error", None),
])
def test_transport_failures_are_recorded_without_urls_or_exception_text(monkeypatch, failure, reason, status):
    monkeypatch.setattr(http, "PHASE1_SERVICE_TOKEN", SECRET)
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(http.urllib.request, "build_opener", lambda *args: SimpleNamespace(open=fail))
    with diag.capture_explain_diagnostics() as events:
        assert http._request_envelope_from_base(http.PHASE1_ORCHESTRATOR_URL, "/v1/explain") is None
    assert events == [{"route": "companion", "stage": "transport", "outcome": reason, "http_status": status}]
    assert SECRET not in json.dumps(events)


@pytest.mark.parametrize("body,reason", [(b"not-json", "invalid_json"), (b'{"current_cause":"BTC"}', "json_received")])
def test_http_status_survives_body_parsing(monkeypatch, body, reason):
    monkeypatch.setattr(http, "PHASE1_SERVICE_TOKEN", SECRET)
    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self):
            return body
    monkeypatch.setattr(http.urllib.request, "build_opener", lambda *args: SimpleNamespace(open=lambda *a, **k: Response()))
    with diag.capture_explain_diagnostics() as events:
        http._request_envelope_from_base(http.PHASE1_ORCHESTRATOR_URL, "/v1/explain")
    assert events[0]["http_status"] == 200
    assert events[0]["outcome"] == reason


def test_missing_token_is_visible_without_sending_a_request(monkeypatch):
    monkeypatch.setattr(http, "PHASE1_SERVICE_TOKEN", "")
    def forbidden(*args):
        pytest.fail("network must not be invoked")
    monkeypatch.setattr(http.urllib.request, "build_opener", forbidden)
    with diag.capture_explain_diagnostics() as events:
        assert http._request_envelope_from_base(http.PHASE1_ORCHESTRATOR_URL, "/v1/explain") is None
    assert events[0]["outcome"] == "missing_service_token"


def test_capture_is_opt_in_nested_and_restored_after_exception():
    with diag.capture_explain_diagnostics() as outer:
        diag.record_explain_event("primary", "normalization", "accepted")
        with pytest.raises(RuntimeError):
            with diag.capture_explain_diagnostics() as inner:
                diag.record_explain_event("companion", "normalization", "foreign_asset")
                raise RuntimeError("fixture")
        diag.record_explain_event("dashboard", "selection", "static_fallback")
    diag.record_explain_event("companion", "normalization", "accepted")
    assert len(outer) == 2 and len(inner) == 1
    assert outer[-1]["outcome"] == "static_fallback"


def test_untrusted_child_receipt_is_allowlisted_and_bounded():
    unsafe = {"route": SECRET, "stage": SECRET, "outcome": {"secret": SECRET}, "http_status": SECRET,
              "headers": {"Authorization": SECRET}, "response": {"provider": SECRET,
              "fields_present": 5, "execution_disabled": SECRET, "evidence_count": SECRET,
              "citation_hashes": [{"url": SECRET, "id_sha256": SECRET}]}}
    result = diag.sanitize_events([unsafe] * 40)
    assert len(result) == 16
    assert SECRET not in json.dumps(result)
    assert result[0]["response"]["fields_present"] == []
