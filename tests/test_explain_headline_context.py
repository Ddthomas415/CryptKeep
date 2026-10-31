"""Offline regressions for narrow subject-versus-cited-headline classification."""
from copy import deepcopy

import pytest

from dashboard.services.views import _explain_diagnostics as diagnostics
from dashboard.services.views import market_view
from dashboard.services.views._shared_signals import (
    _explain_archived_headline_context,
    _explain_mentions_foreign_asset as refused,
)
from scripts.research import companion_evidence_checks as checks
from scripts.research import companion_existing_controller as controller
from tests.test_companion_archive_contract import assembled, inputs, offline
from tests.test_explain_diagnostics import client


@pytest.fixture
def response(monkeypatch):
    offline(monkeypatch)
    view, approvals, _ = inputs()
    return assembled(view, [5, 7]), view, approvals


def test_related_archived_quote_passes_actual_normalizer_and_unchanged_witness(response, monkeypatch):
    raw, view, approvals = response
    client(monkeypatch, companion=raw)
    with diagnostics.capture_explain_diagnostics() as events:
        normal = market_view.get_research_explain("BTC", checks.QUESTION)
    assert normal["current_cause"] == raw["current_cause"]
    assert normal["assistant_status"]["provider"] == "fallback"
    assert not any(e["outcome"] in {"foreign_asset", "static_fallback"} for e in events)
    assert controller.explanation_gates({"raw": raw, "normalized": normal, "http_status": 200})
    assert all(checks.evaluate(raw, view, list(view["original"].values()), approvals).values())


@pytest.mark.parametrize("asset", ["ETH", "SOL", "ADA", None, "", 123, "btc"])
def test_explicit_wrong_or_malformed_subject_cannot_be_relabelled(response, monkeypatch, asset):
    raw = deepcopy(response[0])
    raw["asset"] = asset
    assert refused(raw, "BTC")
    client(monkeypatch, companion=raw)
    assert market_view.get_research_explain("BTC", checks.QUESTION)["assistant_status"]["provider"] == "dashboard_fallback"


@pytest.mark.parametrize("field", ["current_cause", "past_precedent", "future_catalyst"])
@pytest.mark.parametrize("ticker", ["ETH", "SOL"])
def test_foreign_assertion_outside_exact_headline_remains_rejected(response, field, ticker):
    raw = deepcopy(response[0])
    raw[field] += f" {ticker} demand increased."
    assert refused(raw, "BTC")


@pytest.mark.parametrize("path,value", [
    (("assistant_status", "provider"), "phase1_copilot"),
    (("assistant_status", "fallback"), False),
    (("assistant_status", "model"), "synthetic-model"),
    (("question_evidence", "method"), "unreviewed"),
    (("question_evidence", "status"), "UNVERIFIED"),
    (("question_evidence", "match_count"), True),
    (("question_evidence", "match_count"), 21),
    (("question_evidence", "causal_relationship_verified"), True),
    (("question_evidence", "semantic_relevance_verified"), True),
    (("archive_view", "status"), "UNVERIFIED"),
    (("evidence", 0, "document_id"), True),
    (("evidence", 0, "id"), "keyword_unbound"),
    (("evidence", 0, "retrieval_method"), "unverified"),
    (("evidence", 0, "semantic_relevance_verified"), True),
    (("evidence", 0, "summary"), "Different BTC and ETH headline"),
    (("evidence", 0, "source"), ""),
    (("evidence", 0, "url"), None),
])
def test_incomplete_or_unbound_context_does_not_bypass_guard(response, path, value):
    raw = deepcopy(response[0])
    target = raw
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert refused(raw, "BTC")


@pytest.mark.parametrize("field", ["asset", "assistant_status", "question_evidence", "archive_view", "evidence"])
def test_missing_context_contract_keeps_legacy_refusal(response, field):
    raw = deepcopy(response[0])
    del raw[field]
    assert refused(raw, "BTC")


def test_foreign_only_title_cannot_claim_requested_subject(response):
    raw = deepcopy(response[0])
    title = raw["evidence"][0]["summary"]
    raw["current_cause"] = raw["current_cause"].replace(title, "ETH demand increased")
    raw["evidence"][0]["summary"] = "ETH demand increased"
    assert refused(raw, "BTC")


def test_quote_not_a_global_token_whitelist(response):
    raw = deepcopy(response[0])
    raw["current_cause"] += raw["current_cause"]
    assert refused(raw, "BTC")


def test_altered_disclaimer_prevents_context_exclusion(response):
    raw = deepcopy(response[0])
    raw["current_cause"] = raw["current_cause"].replace("These matches do not establish a cause", "These matches prove a cause")
    assert refused(raw, "BTC")


def test_no_witness_approval_is_added_by_guard(response):
    _, view, approvals = response
    raw = assembled(view, [5, 47])
    assert not refused(raw, "BTC")
    assert checks.evaluate(raw, view, list(view["original"].values()), approvals) == dict.fromkeys(checks.KEYS, False)


@pytest.mark.parametrize("ticker", ["ETH", "SOL"])
def test_excluding_headline_preserves_outside_token_boundary(response, monkeypatch, ticker):
    raw = deepcopy(response[0])
    block = _explain_archived_headline_context(raw, "BTC")
    assert block
    raw["current_cause"] = ticker + block + "demand increased."
    assert refused(raw, "BTC")
    client(monkeypatch, companion=raw)
    assert market_view.get_research_explain("BTC", checks.QUESTION)["assistant_status"]["provider"] == "dashboard_fallback"
