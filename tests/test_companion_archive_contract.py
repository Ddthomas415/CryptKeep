"""Offline archive-backed fixtures, NOT replay of the missing live response.

Generate the bounded diagnostic report with:
  ./.venv/bin/python -m tests.test_companion_archive_contract --output PATH
No app, Settings, database, Docker, token or HTTP entrypoint is invoked.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace

import pytest

from dashboard.services.views import _explain_diagnostics as diagnostics
from dashboard.services.views import market_view
from phase1_research_copilot.memory_retrieval import article_view
from scripts.research import companion_evidence_checks as checks
from scripts.research import companion_existing_controller as controller
from tests.test_companion_evidence_checks import orchestrator_functions, query_audit
from tests.test_explain_diagnostics import client


ROOT = Path(__file__).resolve().parents[1]
BASE = Path("docs/review_artifacts/companion_worker_preparation_20261023")
ARCHIVE = Path("research/companion_article_body_v1_20261011_gd1abqx9")
RECEIPT = BASE / "runtime_attempt_v6d/receipt.jsonl"
APPROVALS = BASE / "runtime_packet_v6d/topical_approvals.json"
FIXED = {
    RECEIPT: "0ca55ea24bf18b7ff5442d974267497de00f2f3a5e2af1c372459f35aa43b1a9",
    APPROVALS: "f4de03c65058769eb434e5931065deaeb5795087983a92a3b2f54dacd8feff45",
    ARCHIVE / "manifest.json": article_view.APPROVED_MANIFEST_SHA256,
}
SOURCES = (
    "dashboard/services/views/_shared_signals.py",
    "dashboard/services/views/market_view.py",
    "dashboard/services/views/_explain_diagnostics.py",
    "phase1_research_copilot/orchestrator/main.py",
    "phase1_research_copilot/shared/answer_metadata.py",
    "phase1_research_copilot/memory_retrieval/article_view.py",
    "phase1_research_copilot/memory_retrieval/question_query.py",
    "scripts/research/companion_existing_controller.py",
    "scripts/research/companion_evidence_checks.py",
    "tests/test_companion_evidence_checks.py",
    "tests/test_explain_diagnostics.py",
    "tests/test_companion_archive_contract.py",
)


def digest(value):
    return hashlib.sha256(str(value).encode("utf-8", errors="surrogatepass")).hexdigest()


def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline contract attempted network or child process")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "check_output", "check_call", "call"):
        monkeypatch.setattr(subprocess, name, forbidden)


def inputs():
    for path, expected in FIXED.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError(f"frozen_input_changed:{path}")
    view = article_view.read_archive(
        ROOT / ARCHIVE, required=True,
        expected_manifest_sha256=article_view.APPROVED_MANIFEST_SHA256)
    approvals = json.loads((ROOT / APPROVALS).read_text())
    assert len(approvals) == 1 and approvals[0]["document_id"] == 7
    events = [json.loads(line) for line in (ROOT / RECEIPT).read_text().splitlines()]
    query = [row for row in events if row.get("phase") == "query_diagnostics"]
    assert len(query) == 1
    rejected = [e for e in query[0]["installation_evidence"]["events"]
                if e.get("outcome") == "foreign_asset"]
    assert len(rejected) == 1
    return view, approvals, rejected[0]["response"]["citation_hashes"]


def correlation(view, citations):
    result = []
    for citation in citations:
        matches = []
        for row in view["rows"]:
            if digest(row["id"]) != citation["document_id_sha256"]:
                continue
            names = (f"keyword_{row['id']}", "news_1", "news_2", "past_1", "future_1")
            matches.append({
                "archived_document_id": row["id"], "title": row["title"],
                "asset_tags": row["asset_tags"], "body_verified": row["body_verified"],
                "citation_id_matches": [n for n in names if digest(n) == citation["id_sha256"]],
                "url_hash_matches": digest(row["url"]) == citation["url_sha256"],
            })
        result.append({"recorded_hashes": citation, "archive_matches": matches})
    return result


def assembled(view, ids):
    rows = {r["id"]: r for r in view["rows"]}
    tools = {"get_signal_summary": {
        "lexical_matches": [deepcopy(rows[i]) for i in ids],
        "past_context": [], "future_context": [], "keyword_query": query_audit(),
        "market": {"ok": False, "reason": "no_market_data", "latest_price": None,
                   "change_pct": 0.0, "window_samples": 0},
        "archive_view": {"status": "ARTICLE_BODY_V1_PRIMARY", "derived_sha256": view["sha256"],
                         "preserved_unverified_diagnostics": deepcopy(view["diagnostics"]),
                         "diagnostics_complete": True, "original_records_preserved": True}},
             "get_risk_summary": {"execution_mode": "DISABLED", "gate": "NO_TRADING",
                                  "allow_trading": False, "reason": "Phase 1 research copilot mode"}}
    functions = orchestrator_functions()
    raw = functions["_assemble_explain_response"](
        SimpleNamespace(asset="BTC", question=checks.QUESTION),
        functions["_fallback_reasoning"]("BTC", checks.QUESTION, tools), tools,
        llm_status={"provider": "fallback", "model": None, "fallback": True})
    raw["probe_protocol"] = raw["assistant_status"]["probe_protocol"] = controller.PROTOCOL
    return raw


def case(monkeypatch, view, approvals, name, ids):
    raw = assembled(view, ids)
    client(monkeypatch, companion=raw)
    with diagnostics.capture_explain_diagnostics() as events:
        normalized = market_view.get_research_explain("BTC", checks.QUESTION)
    try:
        controller.explanation_gates({"raw": raw, "normalized": normalized, "http_status": 200})
        transport_identity_and_safety = True
    except controller.Refused:
        transport_identity_and_safety = False
    # Saved originals deliberately stand in for a current DB read. These booleans
    # are fixture results only, including the check named "persisted_identity".
    evidence = checks.evaluate(raw, view, deepcopy(list(view["original"].values())), approvals)
    return {
        "name": name, "fixture_kind": "controlled_archive_backed_not_live_replay",
        "lexical_document_ids": ids,
        "foreign_asset_rejected": any(e["outcome"] == "foreign_asset" for e in events),
        "selected_provider": normalized["assistant_status"]["provider"],
        "transport_identity_and_safety_fixture": transport_identity_and_safety,
        "evidence_fixture_checks": evidence,
        "combined_offline_fixture_pass": transport_identity_and_safety and all(evidence.values()),
    }


def build_report(monkeypatch):
    offline(monkeypatch)
    view, approvals, citations = inputs()
    cases = [case(monkeypatch, view, approvals, name, ids) for name, ids in (
        ("registered_btc_witness", [7]),
        ("btc_only_unapproved_citation", [47]),
        ("mixed_asset_with_registered_witness", [5, 7]),
        ("matched_archive_citations_without_witness", [5, 47]),
    )]
    paths = list(FIXED) + [ARCHIVE / n for n in ("original_snapshot.json", "derived_article_body_v1.json")]
    paths += [Path(p) for p in SOURCES]
    return {
        "schema": "companion-offline-archive-contract-v1", "role": "ENGINEER",
        "question": checks.QUESTION, "registered_witness_document_id": 7,
        "source_sha256": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "receipt_archive_correlation": correlation(view, citations), "cases": cases,
        "runtime_status": "INCOMPLETE",
        "limits": [
            "No historical response prose or typed protocol fields were retained; this is not replay.",
            "Hash matches identify compatible saved IDs/URLs, not the missing response titles or body text.",
            "Original document-ID types are unknown; decimal-string and integer IDs hash alike.",
            "Three of five recorded ID hashes have no match in this 55-document archive.",
            "Fixture retrieval selections are explicit, not SQL/vector ranking or historical top-k proof.",
            "Disabled-risk responses are explicit synthetic fixtures, not observations of a running risk service.",
            "Pure function extraction and stub envelopes do not test full service imports or HTTP.",
            "Saved original rows substitute for live DB reads; no current persistence proof.",
            "A combined offline pass proves neither runtime readiness, causal explanation nor profitability.",
        ],
    }


def test_four_contract_cases(monkeypatch):
    # The original matrix/source is retained in the pre-change diagnostic archive.
    # Only the bounded headline-context classification changes; witness rules do not.
    report = build_report(monkeypatch)
    rows = report["cases"]
    assert [r["foreign_asset_rejected"] for r in rows] == [False, False, False, False]
    assert [r["transport_identity_and_safety_fixture"] for r in rows] == [True, True, True, True]
    assert [all(r["evidence_fixture_checks"].values()) for r in rows] == [True, False, True, False]
    assert [r["combined_offline_fixture_pass"] for r in rows] == [True, False, True, False]


def test_hash_matches_are_bounded_and_witness_is_absent(monkeypatch):
    report = build_report(monkeypatch)
    correlations = report["receipt_archive_correlation"]
    matches = [m for c in correlations for m in c["archive_matches"]]
    assert len(correlations) == 5 and {m["archived_document_id"] for m in matches} == {5, 47}
    assert all(m["url_hash_matches"] and m["citation_id_matches"] == [f"keyword_{m['archived_document_id']}"]
               for m in matches)
    assert digest(7) not in {c["recorded_hashes"]["document_id_sha256"] for c in correlations}


def test_frozen_approval_body_matches_without_edits(monkeypatch):
    offline(monkeypatch)
    view, approvals, _ = inputs()
    witness = next(r for r in view["rows"] if r["id"] == 7)
    assert digest(witness["content_text"]) == approvals[0]["body_sha256"]
    assert approvals[0]["excerpt"] in witness["content_text"]
    assert witness["original_content_hash"] == approvals[0]["original_content_hash"]


def test_frozen_input_drift_is_refused(monkeypatch):
    monkeypatch.setitem(FIXED, RECEIPT, "0" * 64)
    with pytest.raises(ValueError, match="frozen_input_changed"):
        inputs()


def test_changed_body_is_not_saved_witness_proof(monkeypatch):
    offline(monkeypatch)
    view, approvals, _ = inputs()
    raw = assembled(view, [7])
    next(r for r in view["rows"] if r["id"] == 7)["content_text"] += " altered"
    assert checks.evaluate(raw, view, list(view["original"].values()), approvals) == dict.fromkeys(checks.KEYS, False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with pytest.MonkeyPatch.context() as patches:
        report = build_report(patches)
    # Exclusive creation preserves previously generated evidence.
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
