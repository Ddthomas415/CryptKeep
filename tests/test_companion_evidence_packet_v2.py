"""Fresh offline evidence integration; no runnable identities or operation supplied."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_runtime_adapter as adapter
from tests.test_companion_archive_contract import APPROVALS, BASE, ROOT, case, inputs, offline


PROPOSAL_BASE = Path("docs/review_artifacts/companion_witness_proposal_v2_20261024")
GUARD_REVIEW = Path("docs/review_artifacts/companion_context_guard_20261024/independent_review_corrected.json")
PINS = {
    PROPOSAL_BASE / "proposal.json": "5095d72eef7a2a9ac1d158aa8aa81fa78944b7c5788db61c735424b75591bf20",
    PROPOSAL_BASE / "independent_review.json": "c24620ca184ccd01d8afc14e6fdc2ecc96073181c09bc0dc880920e9b8598525",
    GUARD_REVIEW: "9a8acc659bda7e7f53059b3297c714b63ace0b0531d7cafc5265bcb60a8c5819",
    BASE / "runtime_attempt_v6d/outcome.json": "6632d19acb5a4510a614f4f1e1bf06213bc0617cef0a40715dad921e465a4114",
    BASE / "runtime_attempt_v6d/postcheck.json": "ae910c0b2bc4a7ef6886a71190abaf0dbf8c2b4b2b2c71231c1ccbeeba60a8ea",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"packet_binding_changed:{path}")
    return json.loads(raw)


def build_packet(monkeypatch):
    offline(monkeypatch)
    verified = {p: checked(p, h) for p, h in PINS.items()}
    proposal = verified[PROPOSAL_BASE / "proposal.json"]
    semantic = verified[PROPOSAL_BASE / "independent_review.json"]
    guard = verified[GUARD_REVIEW]
    assert semantic["decision"] == guard["decision"] == "ACCEPTED_WITH_RISK"
    assert semantic["effective"] is False and not semantic["operational_authorized"]
    assert guard["cg_1"]["resolved"] is True and not guard["operational_authorized"]
    assert not semantic["findings"] and not guard["findings"]
    source_pins = dict(PINS)
    # Reuse exact accepted evidence, not a new inventory-derived policy approval.
    for review in (semantic, guard):
        for path, digest in review["source_and_artifact_sha256"].items():
            path = Path(path)
            checked_raw = (ROOT / path).read_bytes()
            if hashlib.sha256(checked_raw).hexdigest() != digest:
                raise ValueError(f"reviewed_source_changed:{path}")
            assert path not in source_pins or source_pins[path] == digest
            source_pins[path] = digest
    outcome = verified[BASE / "runtime_attempt_v6d/outcome.json"]
    historical = verified[BASE / "runtime_attempt_v6d/postcheck.json"]
    assert outcome["stdout"]["preparation_consumed"] is True
    assert outcome["stdout"]["prepared_ids_preserved"] is False
    assert historical["prepared_ids_absent"] is True
    view, current, _ = inputs()
    candidates = deepcopy(proposal["proposed_records"])
    assert candidates[:len(current)] == current
    assert [r["document_id"] for r in candidates] == [7, 5, 47, 18]
    candidate_bytes = canonical(candidates)
    draft = {
        "schema": "companion-runtime-pins-v2", "decision": "INCOMPLETE", "reviewer": "",
        "subjects": [], "dependency_reviews": {},
        "network_configuration": {"contract": "configured-network-v1", "bindings": {}},
        "topical_approvals_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
    }
    draft_bytes = canonical(draft)
    pins = adapter.ReviewedPins((), hashlib.sha256(draft_bytes).hexdigest(), (),
                                tuple(candidates), draft_bytes, ())
    validator = adapter.PinnedRuntimeAdapter(None, pins)
    assert validator._topical_contract() is True
    assert validator._policy_reviews_match({}) is False
    with pytest.raises(core.Refused, match="reviewed_pins_missing"):
        validator._pins()
    with pytest.raises(core.Refused, match="adapter_not_authorized_or_not_bounded"):
        validator._require()
    comparisons = [case(monkeypatch, view, candidates, name, ids) for name, ids in (
        ("projected_top_three", [5, 47, 18]), ("preserved_witness", [7]),
        ("unsupported_document", [1]), ("unverified_body", [25]))]
    for name in ("scripts/research/companion_runtime_adapter.py",
                 "tests/test_companion_evidence_packet_v2.py"):
        path = Path(name)
        source_pins[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    evidence = {
        "schema": "companion-offline-evidence-integration-v2", "decision": "READY_FOR_INDEPENDENT_REVIEW",
        "scope": "evidence_portion_only_not_executable_runtime_packet", "effective": False,
        "question": core.QUESTION, "candidate_file": "topical_candidates.json",
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "runtime_draft_sha256": hashlib.sha256(draft_bytes).hexdigest(),
        "semantic_review_sha256": PINS[PROPOSAL_BASE / "independent_review.json"],
        "guard_review_sha256": PINS[GUARD_REVIEW],
        "guard_source_sha256": source_pins[Path("dashboard/services/views/_shared_signals.py")],
        "runtime_subjects": [], "attempt": None, "runtime_ready": False,
        "operational_authorized": False,
        "pending": ["Current read-only runtime baseline and exact-ID evidence",
                    "Fresh independently reviewed subject/dependency/runtime bindings",
                    "Separately authorized bounded operation, if later justified"],
        "historical_limits": "Consumed V6d IDs/receipts are historical references only; no reset, reuse or current-state assertion.",
    }
    proof = {
        "schema": "companion-offline-evidence-integration-proof-v2", "role": "ENGINEER",
        "source_sha256": {str(p): h for p, h in source_pins.items()},
        "actual_adapter_topical_shape_pass": True,
        "actual_adapter_runtime_policy_pass": False,
        "actual_adapter_pins_refused": True, "actual_adapter_enablement_refused": True,
        "comparisons": comparisons, "runtime_status": "INCOMPLETE",
        "limits": ["Schema acceptance is not source/topic/current-DB acceptance.",
                   "Positive evidence cases are saved-row/synthetic transport fixtures, not live integration.",
                   "Empty runtime identities are intentional; no prior removed ID or approval is adopted."],
    }
    return {"topical_candidates.json": candidates, "runtime_review.draft.json": draft,
            "evidence_acceptance.draft.json": evidence, "proof.json": proof}


def test_reviewed_records_integrate_without_identity_or_operation_authority(monkeypatch):
    packet = build_packet(monkeypatch)
    assert packet["runtime_review.draft.json"]["subjects"] == []
    assert packet["runtime_review.draft.json"]["decision"] == "INCOMPLETE"
    assert packet["evidence_acceptance.draft.json"]["runtime_ready"] is False
    assert packet["evidence_acceptance.draft.json"]["effective"] is False
    assert packet["evidence_acceptance.draft.json"]["attempt"] is None
    assert packet["proof.json"]["actual_adapter_topical_shape_pass"]
    assert packet["proof.json"]["actual_adapter_pins_refused"]
    assert packet["proof.json"]["actual_adapter_enablement_refused"]


def test_candidate_bytes_use_existing_canonical_adapter_contract(monkeypatch):
    packet = build_packet(monkeypatch)
    records = packet["topical_candidates.json"]
    assert canonical(records) == adapter._canonical(tuple(records))
    assert hashlib.sha256(canonical(records)).hexdigest() == packet["runtime_review.draft.json"]["topical_approvals_sha256"]


def test_unchanged_verifier_still_refuses_unsupported_and_unverified_cases(monkeypatch):
    rows = build_packet(monkeypatch)["proof.json"]["comparisons"]
    assert [r["combined_offline_fixture_pass"] for r in rows] == [True, True, False, False]


def test_untrusted_review_drift_prevents_packet_generation(monkeypatch):
    monkeypatch.setitem(PINS, GUARD_REVIEW, "0" * 64)
    with pytest.raises(ValueError, match="packet_binding_changed"):
        build_packet(monkeypatch)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with pytest.MonkeyPatch.context() as patches:
        packet = build_packet(patches)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name, value in packet.items():
        with (args.output_dir / name).open("xb") as stream:
            stream.write(canonical(value))
