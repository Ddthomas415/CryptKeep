"""Offline cited-title compatibility, not replay of omitted runtime prose."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dashboard.services.views import _explain_diagnostics as diagnostics
from dashboard.services.views import market_view
from dashboard.services.views._shared_signals import _explain_mentions_foreign_asset as refused
from scripts.research import companion_evidence_checks as checks
from scripts.research import companion_existing_controller as controller
from tests.test_companion_archive_contract import inputs, offline
from tests.test_companion_evidence_checks import orchestrator_functions, query_audit
from tests.test_explain_diagnostics import client


@pytest.fixture(params=["past", "future"])
def cited(monkeypatch, request):
    offline(monkeypatch)
    view, approvals, _ = inputs()
    rows = {r["id"]: r for r in view["rows"]}
    kind = request.param
    tools = {
        "get_signal_summary": {
            "lexical_matches": [deepcopy(rows[5]), deepcopy(rows[7])],
            "past_context": [deepcopy(rows[5])] if kind == "past" else [],
            "future_context": [deepcopy(rows[5])] if kind == "future" else [],
            "keyword_query": query_audit(),
            "market": {"ok": False, "reason": "no_market_data", "latest_price": None,
                       "change_pct": 0.0, "window_samples": 0},
            "archive_view": {
                "status": "ARTICLE_BODY_V1_PRIMARY", "derived_sha256": view["sha256"],
                "preserved_unverified_diagnostics": deepcopy(view["diagnostics"]),
                "diagnostics_complete": True, "original_records_preserved": True,
            },
        },
        "get_risk_summary": {"execution_mode": "DISABLED", "gate": "NO_TRADING",
                             "allow_trading": False, "reason": "Phase 1 research copilot mode"},
    }
    functions = orchestrator_functions()
    raw = functions["_assemble_explain_response"](
        SimpleNamespace(asset="BTC", question=checks.QUESTION),
        functions["_fallback_reasoning"]("BTC", checks.QUESTION, tools), tools,
        llm_status={"provider": "fallback", "model": None, "fallback": True})
    raw["probe_protocol"] = raw["assistant_status"]["probe_protocol"] = controller.PROTOCOL
    field = "past_precedent" if kind == "past" else "future_catalyst"
    return raw, field, kind, view, approvals


def test_exact_bound_title_passes_client_and_unchanged_evidence_checks(cited, monkeypatch):
    raw, field, _, view, approvals = cited
    assert "BTC" in raw[field] and "ETH" in raw[field]
    assert not refused(raw, "BTC")
    client(monkeypatch, companion=raw)
    with diagnostics.capture_explain_diagnostics() as events:
        normal = market_view.get_research_explain("BTC", checks.QUESTION)
    assert normal[field] == raw[field]
    assert normal["assistant_status"]["provider"] == "fallback"
    assert not any(e["outcome"] in {"foreign_asset", "static_fallback"} for e in events)
    assert controller.explanation_gates({"raw": raw, "normalized": normal, "http_status": 200})
    assert all(checks.evaluate(raw, view, list(view["original"].values()), approvals).values())


@pytest.mark.parametrize("key,value", [
    ("document_id", True), ("document_id", "5"), ("document_id", 7),
    ("id", "past_2"), ("id", "future_2"), ("type", "news"),
    ("source", "different"), ("url", "https://example.test/different"),
    ("timestamp", "2000-01-01T00:00:00+00:00"),
    ("summary", "BTC and ETH rose for another reason"),
])
def test_mismatched_citation_stays_blocked(cited, key, value):
    raw, _, kind, _, _ = cited
    citation = next(r for r in raw["evidence"] if r["type"] == kind)
    citation[key] = value
    assert refused(raw, "BTC")


@pytest.mark.parametrize("change", ["missing", "duplicate", "not_keyword_bound"])
def test_missing_ambiguous_or_unbound_citation_stays_blocked(cited, change):
    raw, _, kind, _, _ = cited
    citation = next(r for r in raw["evidence"] if r["type"] == kind)
    if change == "missing":
        raw["evidence"].remove(citation)
    elif change == "duplicate":
        raw["evidence"].append(deepcopy(citation))
    else:
        citation["document_id"] = 999
    assert refused(raw, "BTC")


@pytest.mark.parametrize("value", [None, [], False, 1, "", " ", "not-a-time",
                                   "2026-10-25T12:00:00", "x" * 129])
def test_malformed_shared_timestamp_stays_blocked(cited, value, monkeypatch):
    raw, field, kind, _, _ = cited
    for row in raw["evidence"]:
        if row.get("document_id") == 5:
            row["timestamp"] = value
    assert refused(raw, "BTC")
    client(monkeypatch, companion=raw)
    assert market_view.get_research_explain("BTC", checks.QUESTION)["assistant_status"]["provider"] == "dashboard_fallback"


def test_missing_shared_timestamp_stays_blocked(cited):
    raw = cited[0]
    for row in raw["evidence"]:
        if row.get("document_id") == 5:
            del row["timestamp"]
    assert refused(raw, "BTC")


@pytest.mark.parametrize("other_kind", ["news", "other", "past", "future"])
def test_citation_id_duplicate_across_types_stays_blocked(cited, other_kind, monkeypatch):
    raw, _, kind, _, _ = cited
    citation = next(r for r in raw["evidence"] if r["type"] == kind)
    raw["evidence"].append({**deepcopy(citation), "type": other_kind})
    assert refused(raw, "BTC")
    client(monkeypatch, companion=raw)
    assert market_view.get_research_explain("BTC", checks.QUESTION)["assistant_status"]["provider"] == "dashboard_fallback"


@pytest.mark.parametrize("transform", [
    lambda s: s + " ETH demand explains this move.",
    lambda s: "ETH demand explains this move. " + s,
    lambda s: s + " ", lambda s: s.lower(),
])
def test_nonexact_or_extended_title_stays_blocked(cited, transform):
    raw, field, _, _, _ = cited
    raw[field] = transform(raw[field])
    assert refused(raw, "BTC")


@pytest.mark.parametrize("change", [
    "no_context", "duplicated_context", "wrong_asset", "live_execution", "model_provider",
    "no_archive", "semantic_claim", "causal_claim", "foreign_only_title",
])
def test_missing_research_contract_does_not_exempt_title(cited, change):
    raw, field, kind, _, _ = cited
    if change == "no_context":
        raw["current_cause"] = "BTC context unavailable."
    elif change == "duplicated_context":
        raw["current_cause"] *= 2
    elif change == "wrong_asset":
        raw["asset"] = "ETH"
    elif change == "live_execution":
        raw["execution_disabled"] = False
    elif change == "model_provider":
        raw["assistant_status"]["provider"] = "openai"
    elif change == "no_archive":
        raw.pop("archive_view")
    elif change == "semantic_claim":
        raw["question_evidence"]["semantic_relevance_verified"] = True
    elif change == "causal_claim":
        raw["question_evidence"]["causal_relationship_verified"] = True
    else:
        old = raw[field]
        raw[field] = "ETH demand increased"
        raw["current_cause"] = raw["current_cause"].replace(old, raw[field])
        for r in raw["evidence"]:
            if r.get("document_id") == 5:
                r["summary"] = raw[field]
    assert refused(raw, "BTC")


@pytest.mark.parametrize("field", ["current_cause", "past_precedent", "future_catalyst"])
def test_unsupported_foreign_assertion_elsewhere_stays_blocked(cited, field):
    raw = cited[0]
    raw[field] += " SOL demand is the cause."
    assert refused(raw, "BTC")


def test_saved_citation_selection_passes_offline_with_existing_witnesses(monkeypatch):
    offline(monkeypatch)
    view, _, _ = inputs()
    rows = {r["id"]: r for r in view["rows"]}
    path = (Path(__file__).resolve().parents[1]
            / "docs/review_artifacts/companion_integration_inputs_v6f_20261025"
            / "runtime_packet_v6f/topical_approvals.json")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "dc3f5678277fb14afb523d54acfc3ef9303627fb810ad075228702054d18505a"
    approvals = json.loads(path.read_text())
    tools = {
        "get_signal_summary": {
            "lexical_matches": [deepcopy(rows[i]) for i in (5, 47, 18)],
            "past_context": [deepcopy(rows[5])], "future_context": [deepcopy(rows[26])],
            "keyword_query": query_audit(),
            "market": {"ok": False, "reason": "no_market_data", "latest_price": None,
                       "change_pct": 0.0, "window_samples": 0},
            "archive_view": {
                "status": "ARTICLE_BODY_V1_PRIMARY", "derived_sha256": view["sha256"],
                "preserved_unverified_diagnostics": deepcopy(view["diagnostics"]),
                "diagnostics_complete": True, "original_records_preserved": True,
            },
        },
        "get_risk_summary": {"execution_mode": "DISABLED", "gate": "NO_TRADING",
                             "allow_trading": False, "reason": "Phase 1 research copilot mode"},
    }
    functions = orchestrator_functions()
    raw = functions["_assemble_explain_response"](
        SimpleNamespace(asset="BTC", question=checks.QUESTION),
        functions["_fallback_reasoning"]("BTC", checks.QUESTION, tools), tools,
        llm_status={"provider": "fallback", "model": None, "fallback": True})
    raw["probe_protocol"] = raw["assistant_status"]["probe_protocol"] = controller.PROTOCOL
    assert [r["document_id"] for r in raw["evidence"]] == [5, 47, 18, 5, 26]
    client(monkeypatch, companion=raw)
    normal = market_view.get_research_explain("BTC", checks.QUESTION)
    assert controller.explanation_gates({"raw": raw, "normalized": normal, "http_status": 200})
    assert all(checks.evaluate(raw, view, list(view["original"].values()), approvals).values())
    # Known current-DB originals and no market data above are substituted inputs,
    # not fresh runtime reads or reconstruction of the missing response prose.
