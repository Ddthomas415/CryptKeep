"""Versioned offline proposal only: never changes effective approvals or ranking."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.research import companion_evidence_checks as checks
from tests.test_companion_archive_contract import (
    ARCHIVE, APPROVALS, RECEIPT, ROOT, SOURCES, assembled, case, inputs, offline,
)
from tests.test_companion_witness_selection import saved_projection


EXCERPTS = {
    5: ("Hours later, it had plunged below $105,000, with much of the decline coming in minutes in thin "
        "Friday evening (U.S. time) trade after President Donald Trump announced 100% tariffs on Chinese imports. "
        "More than $19 billion in leveraged positions were liquidated in a single day."),
    47: ("A Bitcoin (BTC) and altcoins sell-off triggered more than $1 billion in liquidations over 24 hours "
         "as short-term holders sent tens of thousands of BTC to exchanges at a loss."),
    18: ("Bitcoin BTC $82,985.25 held near $82,600 after President Donald Trump said he would not strike Iran "
         "before the U.S. midterm elections, pulling the largest cryptocurrency off Thursday\u2019s low of roughly "
         "$80,400 and turning the liquidation pressure onto bearish traders ."),
}


def build_proposal(view, current):
    _, projection = saved_projection(view)
    selected = [r["id"] for r in projection[:3]]
    assert selected == [5, 47, 18] and set(EXCERPTS) == set(selected)
    rows = {r["id"]: r for r in view["rows"]}
    proposed = deepcopy(current)
    bodies = []
    for ident in selected:
        row, excerpt = rows[ident], EXCERPTS[ident]
        body = row["content_text"]
        assert row["body_verified"] is True and body.count(excerpt) == 1
        record = {"document_id": ident, "question": checks.QUESTION,
                  "original_content_hash": row["original_content_hash"],
                  "body_sha256": hashlib.sha256(body.encode()).hexdigest(), "excerpt": excerpt}
        proposed.append(record)
        bodies.append({"document_id": ident, "title": row["title"], "source": row["source"],
                       "url": row["url"], "published_at": row["published_at"],
                       "fetched_at": row["fetched_at"], "full_saved_body": body,
                       "body_sha256": record["body_sha256"], "excerpt": excerpt,
                       "excerpt_offset": body.index(excerpt), "body_verified": True})
    return {
        "schema": "companion-topical-witness-proposal-v2",
        "acceptance": "READY_FOR_INDEPENDENT_REVIEW", "effective": False,
        "question": checks.QUESTION, "preserved_document_ids": [r["document_id"] for r in current],
        "candidate_selection": "all_three_from_body_verified_saved_order_projection_not_live_ranking",
        "added_candidate_document_ids": selected, "proposed_records": proposed,
        "limits": ["Historical topical support only; article claims and causal explanations not independently verified.",
                   "Not a current-market answer, current DB identity, live selection, runtime or profitability proof.",
                   "This proposal is not an effective approval list and must not replace a runtime packet."],
    }, bodies


def build_packet(monkeypatch):
    offline(monkeypatch)
    view, current, _ = inputs()
    proposal, bodies = build_proposal(view, current)
    proposed = proposal["proposed_records"]
    comparisons = []
    for name, ids in (("saved_top_three_projection", [5, 47, 18]),
                      ("preserved_witness_control", [7]),
                      ("unproposed_document", [1]), ("unverified_body", [25])):
        comparisons.append({
            "name": name, "evidence_lane": "COUNTERFACTUAL_OFFLINE_FIXTURE_NOT_ACTIVATION",
            "current": case(monkeypatch, view, current, name, ids),
            "proposed": case(monkeypatch, view, proposed, name, ids),
        })
    paths = [APPROVALS, RECEIPT] + [ARCHIVE / n for n in (
        "manifest.json", "original_snapshot.json", "derived_article_body_v1.json", "query_comparison.json")]
    paths += [Path(p) for p in SOURCES] + [Path("tests/test_companion_witness_selection.py"),
                                          Path("tests/test_companion_witness_proposal.py")]
    proof = {
        "schema": "companion-topical-witness-proposal-proof-v2", "role": "ENGINEER",
        "effective_approvals_changed": False, "runtime_status": "INCOMPLETE",
        "source_sha256": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "comparisons": comparisons,
        "limits": ["Verifier unchanged; proposed records supplied explicitly only to fixture calls.",
                   "Positive fixture flags substitute saved original rows for live DB reads.",
                   "Mechanical hash/excerpt checks cannot decide semantic relevance; separate full-body review required."],
    }
    return {"proposal.json": proposal, "candidate_bodies.json": bodies, "proof.json": proof}


def test_preserves_existing_record_and_proposes_all_selected_candidates(monkeypatch):
    offline(monkeypatch)
    view, current, _ = inputs()
    proposal, bodies = build_proposal(view, current)
    assert proposal["proposed_records"][:len(current)] == current
    assert proposal["added_candidate_document_ids"] == [5, 47, 18]
    assert [r["document_id"] for r in proposal["proposed_records"]] == [7, 5, 47, 18]
    assert proposal["effective"] is False and len(bodies) == 3
    for row in bodies:
        assert row["full_saved_body"].count(row["excerpt"]) == 1
        assert hashlib.sha256(row["full_saved_body"].encode()).hexdigest() == row["body_sha256"]


def test_proposal_changes_only_explicit_fixture_support_not_identity_rules(monkeypatch):
    proof = build_packet(monkeypatch)["proof.json"]
    rows = proof["comparisons"]
    assert [r["current"]["combined_offline_fixture_pass"] for r in rows] == [False, True, False, False]
    assert [r["proposed"]["combined_offline_fixture_pass"] for r in rows] == [True, True, False, False]


def test_proposal_envelope_cannot_be_used_as_effective_approval_list(monkeypatch):
    offline(monkeypatch)
    view, current, _ = inputs()
    proposal, _ = build_proposal(view, current)
    raw = assembled(view, [5, 47, 18])
    assert checks.evaluate(raw, view, list(view["original"].values()), proposal) == dict.fromkeys(checks.KEYS, False)


@pytest.mark.parametrize("field,value", [("body_sha256", "0" * 64),
                                         ("question", "What explains Ethereum?"),
                                         ("excerpt", "Invented excerpt")])
def test_changed_proposed_witness_still_fails_closed(monkeypatch, field, value):
    offline(monkeypatch)
    view, current, _ = inputs()
    proposal, _ = build_proposal(view, current)
    proposal["proposed_records"][1][field] = value
    raw = assembled(view, [5, 47, 18])
    assert checks.evaluate(raw, view, list(view["original"].values()), proposal["proposed_records"]) == dict.fromkeys(checks.KEYS, False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    with pytest.MonkeyPatch.context() as patches:
        packet = build_packet(patches)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name, value in packet.items():
        with (args.output_dir / name).open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
