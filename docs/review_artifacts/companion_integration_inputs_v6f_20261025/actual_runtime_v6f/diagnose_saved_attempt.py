"""Offline diagnosis of saved public receipt, not replay of missing response prose.

Run from the repository root; emits JSON on stdout without changing inputs.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from dashboard.services.views._shared_signals import (
    _explain_archived_headline_context,
    _explain_mentions_foreign_asset,
)
from phase1_research_copilot.memory_retrieval import article_view
from tests.test_companion_archive_contract import assembled, offline


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / "research/companion_article_body_v1_20261011_gd1abqx9"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with pytest.MonkeyPatch.context() as monkeypatch:
        offline(monkeypatch)
        receipt = HERE / "receipt.jsonl"
        source = ROOT / ".cbp_state/runtime/companion_cutovers/workerprep20261025v6f/receipt.jsonl"
        assert receipt.read_bytes() == source.read_bytes()
        events = [json.loads(line) for line in receipt.read_text().splitlines()]
        query = [e for e in events if e.get("phase") == "query_diagnostics"]
        assert len(query) == 1
        diagnostics = query[0]["installation_evidence"]["events"]
        response = next(e["response"] for e in diagnostics
                        if e.get("route") == "companion" and e.get("stage") == "transport")
        view = article_view.read_archive(
            ARCHIVE, required=True,
            expected_manifest_sha256=article_view.APPROVED_MANIFEST_SHA256)
        rows = {hashlib.sha256(str(r["id"]).encode()).hexdigest(): r for r in view["rows"]}
        correlation = []
        for c in response["citation_hashes"]:
            row = rows.get(c["document_id_sha256"])
            assert row is not None
            names = [f"keyword_{row['id']}", "news_1", "news_2", "news_3", "past_1", "future_1"]
            correlation.append({
                "document_id": row["id"], "title": row["title"],
                "citation_id_candidates": [n for n in names if hashlib.sha256(n.encode()).hexdigest() == c["id_sha256"]],
                "url_hash_matches": hashlib.sha256(row["url"].encode()).hexdigest() == c["url_sha256"],
            })
        assert all(r["url_hash_matches"] for r in correlation)
        assert [r["document_id"] for r in correlation] == [5, 47, 18, 5, 26]
        assert [r["citation_id_candidates"] for r in correlation] == [
            ["keyword_5"], ["keyword_47"], ["keyword_18"], ["past_1"], ["future_1"]]

        raw = assembled(view, [5, 47, 18])
        by_id = {r["id"]: r for r in view["rows"]}
        cases = []
        for name, past in (
            ("keyword_headlines_only", raw["past_precedent"]),
            ("same_archived_mixed_title_as_past", by_id[5]["title"]),
            ("btc_only_past_control", by_id[47]["title"]),
        ):
            candidate = deepcopy(raw)
            candidate["past_precedent"] = past
            candidate["future_catalyst"] = by_id[26]["title"]
            cases.append({
                "name": name,
                "labelled_current_context_recognized": bool(_explain_archived_headline_context(candidate, "BTC")),
                "foreign_asset_rejected": _explain_mentions_foreign_asset(candidate, "BTC"),
            })
        assert [c["foreign_asset_rejected"] for c in cases] == [False, True, False]
        assert all(c["labelled_current_context_recognized"] for c in cases)
        sources = [receipt, source, Path(__file__),
                   ROOT / "dashboard/services/views/_shared_signals.py",
                   ROOT / "phase1_research_copilot/orchestrator/main.py",
                   ROOT / "tests/test_companion_archive_contract.py",
                   ROOT / "tests/test_companion_evidence_checks.py",
                   ROOT / "phase1_research_copilot/memory_retrieval/article_view.py"]
        sources += [ARCHIVE / n for n in ("manifest.json", "original_snapshot.json", "derived_article_body_v1.json")]
        print(json.dumps({
            "schema": "companion-v6f-saved-attempt-diagnosis-v1",
            "role": "ENGINEER", "runtime_status": "INCOMPLETE",
            "receipt_events": len(events),
            "actual_diagnostic_stages": [{k: e.get(k) for k in ("route", "stage", "outcome", "http_status")} for e in diagnostics],
            "verifier_result_event_count": sum(e.get("phase") == "evidence_verification_checks" for e in events),
            "citation_archive_correlation": correlation,
            "synthetic_guard_cases": cases,
            "hashes": {str(p.relative_to(ROOT)): sha(p) for p in sources},
            "limits": [
                "Raw runtime response prose and field types were not retained; fixtures are not a live-response replay.",
                "ID/URL/citation-name hash matches support archive correlation, not response body or topical proof.",
                "Past-precedent field is a demonstrated static/synthetic failure mechanism, not a proven unique runtime cause.",
                "No native, service, token, network, database, startup or live query operation is performed.",
                "Recovery receipt is not proof of post-recovery health, connectivity or volume-byte equality.",
            ],
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
