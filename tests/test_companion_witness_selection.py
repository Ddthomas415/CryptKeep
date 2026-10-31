"""Saved-order projection and real clipping functions, not live SQL replay."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.research import companion_evidence_checks as checks
from tests.test_companion_archive_contract import (
    ARCHIVE, APPROVALS, RECEIPT, ROOT, assembled, case, inputs, offline,
)


COMPARISON = ARCHIVE / "query_comparison.json"
COMPARISON_SHA256 = "88bb8e5a79d711d4339807e34caed4f3b20d89308c3eb4eb13300e397911fb5b"


def saved_projection(view):
    data = (ROOT / COMPARISON).read_bytes()
    if hashlib.sha256(data).hexdigest() != COMPARISON_SHA256:
        raise ValueError("saved_comparison_changed")
    matches = [r for r in json.loads(data) if r["question"] == checks.QUERY_AUDIT["query"]]
    assert len(matches) == 1
    saved = matches[0]["derived"]
    verified = {r["id"] for r in view["rows"] if r["body_verified"] is True}
    # Preserve saved ordering. No tokenization, stemming or SQL ranks are recomputed.
    return saved, [r for r in saved if r["id"] in verified]


def probe_calls():
    """Run only the extracted pure coroutine with an immediate in-memory transport."""
    path = ROOT / "phase1_research_copilot/shared/tools.py"
    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, ast.AsyncFunctionDef) and n.name == "get_probe_tool_results"]
    assert len(nodes) == 1
    calls = []

    async def request(method, url, payload=None):
        calls.append({"method": method, "url": url, "payload": payload})
        if method == "POST":
            return {"ok": True}
        return {"gate": "NO_TRADING", "allow_trading": False, "execution_mode": "DISABLED"}

    namespace = {
        "Any": object, "probe_active": lambda: True, "_asset_symbol": lambda a: a,
        "_request_json": request,
        "settings": SimpleNamespace(memory_service_url="http://fixture.invalid/memory",
                                    risk_service_url="http://fixture.invalid/risk"),
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    coroutine = namespace["get_probe_tool_results"]("BTC", checks.QUESTION, 60)
    try:
        coroutine.send(None)
    except StopIteration as completed:
        assert completed.value["get_signal_summary"]["ok"] is True
    else:
        coroutine.close()
        raise AssertionError("fixture transport unexpectedly suspended")
    return calls


def build_report(monkeypatch):
    offline(monkeypatch)
    view, approvals, _ = inputs()
    saved, eligible = saved_projection(view)
    ids = [r["id"] for r in eligible]
    paths = [COMPARISON, APPROVALS, RECEIPT] + [ARCHIVE / p for p in (
        "manifest.json", "original_snapshot.json", "derived_article_body_v1.json")]
    paths += [Path(p) for p in (
        "phase1_research_copilot/shared/tools.py", "phase1_research_copilot/orchestrator/main.py",
        "phase1_research_copilot/memory_retrieval/main.py",
        "phase1_research_copilot/memory_retrieval/article_view.py",
        "phase1_research_copilot/memory_retrieval/question_query.py",
        "scripts/research/companion_evidence_checks.py",
        "tests/test_companion_archive_contract.py", "tests/test_companion_evidence_checks.py",
        "tests/test_companion_witness_selection.py")]
    cases = []
    for name, selection in (("projected_first_three", ids[:3]),
                            ("projected_all_four_still_clipped", ids),
                            ("witness_only_control_not_ranking_proposal", [7])):
        result = case(monkeypatch, view, approvals, name, selection)
        raw = assembled(view, selection)
        cited = [r["document_id"] for r in raw["evidence"] if r["type"] == "keyword_match"]
        result.update(cited_keyword_document_ids=cited, witness_in_fixture_input=7 in selection,
                      witness_cited_as_keyword=7 in cited)
        cases.append(result)
    return {
        "schema": "companion-witness-selection-diagnosis-v1", "role": "AUDITOR",
        "question": checks.QUESTION, "normalized_query": checks.QUERY_AUDIT["query"],
        "saved_comparison_order": [r["id"] for r in saved],
        "saved_comparison_ranks": [r["lexical_rank"] for r in saved],
        "body_verified_saved_order_projection": ids,
        "projection_excluded_document_ids": [r["id"] for r in saved if r["id"] not in ids],
        "probe_call_fixture": probe_calls(), "cases": cases,
        "source_sha256": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "runtime_status": "INCOMPLETE",
        "limits": [
            "The query comparison is a saved October11 diagnostic, not the V6d response or current DB ranking.",
            "Filtering its saved ordering is a projection, not a rerun of PostgreSQL stemming, ts_rank_cd or current temporal filters.",
            "Pure coroutine extraction uses synthetic transport/risk responses, not full app imports or live requests.",
            "The four-row builder fixture proves clipping even when witness7 is supplied; it does not prove live retrieval returned it.",
            "Saved originals substitute for live DB identity; no current persistence, causal or profitability proof.",
            "Witness-only is an existing positive control, not approval to force ranking or widen the exact witness list.",
        ],
    }


def test_saved_projection_keeps_original_order_and_excludes_unverified_body(monkeypatch):
    offline(monkeypatch)
    view, _, _ = inputs()
    saved, eligible = saved_projection(view)
    assert [r["id"] for r in saved] == [25, 5, 47, 18, 7]
    assert [r["id"] for r in eligible] == [5, 47, 18, 7]


def test_existing_probe_requests_three_not_the_registered_witness(monkeypatch):
    offline(monkeypatch)
    calls = probe_calls()
    assert len(calls) == 2
    assert calls[0]["method"] == "POST"
    assert calls[0]["payload"] == {"asset": "BTC", "question": checks.QUESTION,
                                   "lookback_minutes": 60, "limit": 3}
    assert "document_id" not in calls[0]["payload"]


def test_existing_builder_clips_tail_witness_independently_of_retrieval_limit(monkeypatch):
    report = build_report(monkeypatch)
    rows = report["cases"]
    assert [r["cited_keyword_document_ids"] for r in rows] == [[5, 47, 18], [5, 47, 18], [7]]
    assert [r["witness_in_fixture_input"] for r in rows] == [False, True, True]
    assert [r["combined_offline_fixture_pass"] for r in rows] == [False, False, True]
    assert all(r["transport_identity_and_safety_fixture"] for r in rows)


def test_changed_saved_comparison_is_refused(monkeypatch):
    import sys
    monkeypatch.setattr(sys.modules[__name__], "COMPARISON_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="saved_comparison_changed"):
        saved_projection({})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with pytest.MonkeyPatch.context() as patches:
        report = build_report(patches)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
