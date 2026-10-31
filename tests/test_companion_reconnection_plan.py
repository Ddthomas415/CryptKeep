"""Offline reuse proof for an update plan, not a new installer or approval."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import pytest

from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter
from tests.test_companion_archive_contract import ROOT, offline


WORKER = Path("docs/review_artifacts/companion_worker_preparation_20261023")
INVENTORY = Path("docs/review_artifacts/companion_runtime_inventory_20261024")
PINS = {
    "manifest": (WORKER / "fresh_preparation_v6d/reviewed_preparation_manifest.json", "629662e509e099be8601be1c9499d7139f03803f4f998f5b31fce15b2551b4a0"),
    "consumers": (WORKER / "fresh_preparation_v6d/provenance.json", "450528ec555d61fca4d3bc6defb94bfaf08ef37b170f18db96f7f2fb94691857"),
    "observation": (INVENTORY / "observation.json", "0a71483b1ee7e54874975647d0105b3f03bc44a9c2274e8a5350ed34bc950793"),
    "inventory_review": (INVENTORY / "independent_review.json", "14dd83b985c1788d9bdba0854ce3cdef98543e0ff3760e0a1a35733fee2af846"),
    "guard_review": (Path("docs/review_artifacts/companion_context_guard_20261024/independent_review_corrected.json"), "9a8acc659bda7e7f53059b3297c714b63ace0b0531d7cafc5265bcb60a8c5819"),
    "evidence_review": (Path("docs/review_artifacts/companion_evidence_packet_v2_20261024/independent_review.json"), "309d6079cc0aee852cba9678ccc0ea77d782d31503edabf53024f3a99ca7b6ef"),
    "candidate_records": (Path("docs/review_artifacts/companion_evidence_packet_v2_20261024/topical_candidates.json"), "dc3f5678277fb14afb523d54acfc3ef9303627fb810ad075228702054d18505a"),
}


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"plan_input_changed:{path}")
    return raw


def build_report():
    raw = {key: checked(*value) for key, value in PINS.items()}
    values = {key: json.loads(value) for key, value in raw.items()}
    for key in ("inventory_review", "guard_review", "evidence_review"):
        assert values[key]["decision"] == "ACCEPTED_WITH_RISK"
    prior = install.Plan.load(raw["manifest"], PINS["manifest"][1])
    observation = values["observation"]
    assert observation["selected_observations_equal"] and observation["metadata_complete_for_selected_fields"]
    assert observation["observations"][0] == observation["observations"][1]
    rows = observation["observations"][-1]
    assert len(rows) == 7
    bindings = dict(prior.network_bindings)
    baseline = []
    for before, row in zip(prior.baseline, rows):
        configured, nets, evidence = network.project(row, bindings)
        foundation = adapter.preservation_digest({**row, "networks": {}})
        assert (row["name"], row["id"], row["image"], row["state"], row["restart_policy"]) == (
            "/" + before.name, before.id, before.image, "running", "no")
        assert row["restarts"] == before.restarts
        assert foundation == before.foundation and configured == before.configured_metadata
        now = install.Snapshot(before.name, row["id"], row["image"], row["state"], row["started"],
            row["restarts"], row["restart_policy"], adapter.preservation_digest(row), foundation,
            tuple(sorted(n["NetworkID"] for n in row["networks"].values())), "", configured, nets, evidence)
        changed = [k for k in asdict(before)
                   if install.canonical(asdict(before)[k]) != install.canonical(asdict(now)[k])]
        assert set(changed) <= {"started"}
        baseline.append({"name": before.name, "observed_id": row["id"], "image": row["image"],
                         "changed_from_prior_preparation_baseline": changed})
    consumers = values["consumers"]["consumer_sha256"]
    assert len(consumers) == 13
    for path, expected in consumers.items():
        checked(Path(path), expected)
    sources = []
    for app in prior.applications:
        for source in app["sources"]:
            checked(Path(source["local"]), source["sha256"])
            sources.append({"application": app["name"], **source})
    assert len(sources) == 43
    paths = {str(path): digest for path, digest in PINS.values()}
    paths.update(consumers)
    paths.update({s["local"]: s["sha256"] for s in sources})
    paths["tests/test_companion_reconnection_plan.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "schema": "companion-minimal-reconnection-plan-proof-v1", "role": "DIRECTOR",
        "state": "READY_FOR_INDEPENDENT_REVIEW", "runtime_status": "INCOMPLETE",
        "source_sha256": paths, "baseline": baseline,
        "application_source_entries": sources, "preparation_consumer_sha256": consumers,
        "application_scope": [a["name"] for a in prior.applications],
        "storage_scope": [r.name for r in prior.baseline[:3]],
        "candidate_witness_ids": [r["document_id"] for r in values["candidate_records"]],
        "attempt_allocated": False, "native_operations": 0, "operational_authorized": False,
        "existing_budgets": {"preparation_seconds": 300, "preparation_recovery_seconds": 120,
                             "cutover_seconds": 600, "cutover_recovery_seconds": 180},
        "limits": ["Reuse checks bind local input bytes, not installed runtime applicability.",
                   "Running baseline is a saved observation, not a live preflight or accepted new manifest.",
                   "No new IDs, attempt, runtime policy, preparation or executable command is created.",
                   "Image cache availability and safe maintenance authorization remain unverified."],
    }


def test_smallest_existing_path_has_reusable_sources_and_consumers(monkeypatch):
    offline(monkeypatch)
    report = build_report()
    assert len(report["application_source_entries"]) == 43
    assert len(report["preparation_consumer_sha256"]) == 13
    assert report["application_scope"] == ["phase1-audit-log", "phase1-risk-stub", "phase1-memory", "phase1-orchestrator"]
    assert report["candidate_witness_ids"] == [7, 5, 47, 18]
    assert report["operational_authorized"] is False and report["attempt_allocated"] is False


def test_review_or_input_drift_prevents_reuse_claim(monkeypatch):
    offline(monkeypatch)
    path, _ = PINS["guard_review"]
    monkeypatch.setitem(PINS, "guard_review", (path, "0" * 64))
    with pytest.raises(ValueError, match="plan_input_changed"):
        build_report()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with pytest.MonkeyPatch.context() as patches:
        offline(patches)
        report = build_report()
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
