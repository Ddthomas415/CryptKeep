"""Offline V6i derivation: accepted evidence, unchanged recipes, drift refusal."""
from copy import deepcopy
import hashlib
import importlib
import json

import pytest

from tests.test_companion_archive_contract import offline


recipe = importlib.import_module(
    "docs.review_artifacts.companion_integration_inputs_v6i_20261027.derive_inputs")
OBSERVATION = recipe.sources.ROOT / recipe.OBSERVATION
OBSERVATION_SHA = "ee934eec73fd0b09e82d9c9a8631f298c53c56622fb6a60a40989e994fb9dbb7"


@pytest.fixture(autouse=True)
def no_operations(monkeypatch):
    offline(monkeypatch)


def old_plan():
    value = json.loads(recipe.sources.checked(*recipe.sources.PINS["manifest"]))
    raw = recipe.install.canonical(value)
    return recipe.install.Plan.load(raw, hashlib.sha256(raw).hexdigest())


def test_saved_inputs_reproduce_preserving_recipes_and_no_approval():
    candidate, proof = recipe.derive(OBSERVATION, OBSERVATION_SHA)
    assert recipe.install.canonical(candidate) == (recipe.HERE / "candidate_manifest.json").read_bytes()
    assert recipe.install.canonical(proof) == (recipe.HERE / "provenance.json").read_bytes()
    assert [r["changed_fields"] for r in proof["baseline_deltas"]] == [[]] * 3 + [["started"]] * 4
    before = json.loads(recipe.sources.checked(*recipe.sources.PINS["manifest"]))
    expected = deepcopy(before)
    expected.update(attempt=recipe.sources.PROPOSED, decision="INCOMPLETE", reviewer="",
                    baseline=candidate["baseline"], applications=recipe.sources.refresh()["applications"])
    assert candidate == expected
    assert proof["consumer_sha256"] == recipe.sources.refresh()["consumer_sha256"]
    assert proof["runtime_consumer_sha256"] == recipe.sources.refresh()["runtime_consumer_sha256"]
    assert proof["new_container_ids"] is None and proof["new_image_ids"] is None
    assert "UNVERIFIED" in proof["changed_memory_image_policy"]
    assert all(proof[k] is False for k in ("preparation_authorized", "startup_authorized", "query_authorized"))
    raw = recipe.install.canonical(candidate)
    with pytest.raises(recipe.install.core.Refused):
        recipe.install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    fixture = deepcopy(candidate)
    fixture.update(decision="ACCEPTED_WITH_RISK", reviewer="SYNTHETIC_ONLY")
    raw = recipe.install.canonical(fixture)
    assert recipe.install.Plan.load(raw, hashlib.sha256(raw).hexdigest()).worker_shutdown


@pytest.mark.parametrize("change", [
    "id", "image", "state", "command", "restarts", "storage_started", "cli", "pair",
    "raw_hash", "raw_payload", "deadline", "source_refresh", "network", "timeout_flag",
])
def test_pure_validation_refuses_synthetic_drift(change):
    observed = json.loads(OBSERVATION.read_bytes())
    row = observed["observations"][0][3]
    if change in {"id", "image"}:
        row[change] = "f" * 64
    elif change == "state":
        row["state"] = "exited"
    elif change == "command":
        row["command"] = ["changed"]
    elif change == "restarts":
        row["restarts"] += 1
    elif change == "storage_started":
        observed["observations"][0][0]["started"] = "2026-10-26T00:00:00Z"
    elif change == "cli":
        observed["cli_sha256"] = "f" * 64
    elif change == "deadline":
        observed["elapsed_seconds"] = 31
    elif change == "source_refresh":
        observed["source_refresh_sha256"] = "f" * 64
    elif change == "network":
        next(iter(row["networks"].values()))["NetworkID"] = "f" * 64
    elif change == "timeout_flag":
        flag = next(f for f in row["flags"] if f and f["key"] == "REQUEST_TIMEOUT_SECONDS")
        flag["ok"] = not flag["ok"]
    if change != "pair":
        observed["observations"][1] = deepcopy(observed["observations"][0])
    else:
        observed["observations"][1][3]["started"] = "2026-10-26T00:00:01Z"
    payloads = [b"".join(json.dumps(r).encode() + b"\n" for r in rows)
                for rows in observed["observations"]]
    observed["raw_sha256"] = [hashlib.sha256(raw).hexdigest() for raw in payloads]
    if change == "raw_hash":
        observed["raw_sha256"][0] = "0" * 64
    if change == "raw_payload":
        payloads[0] += b"{}\n"
    with pytest.raises(ValueError):
        recipe.validate_observation(observed, payloads, old_plan(),
                                    json.loads(OBSERVATION.read_bytes())["source_refresh_sha256"])


@pytest.mark.parametrize("path", [recipe.SOURCE_REVIEW, recipe.BASELINE_REVIEW,
    recipe.OBSERVATION, recipe.MODELS,
    str(recipe.HERE.relative_to(recipe.sources.ROOT) / "actual_baseline/capture_1.jsonl"),
    "phase1_research_copilot/memory_retrieval/main.py",
    "scripts/research/companion_evidence_checks.py"])
def test_bound_evidence_or_current_source_drift_refuses(monkeypatch, path):
    original = recipe.sources.checked

    def changed(name, expected):
        if name == path:
            raise ValueError("injected_digest_mismatch")
        return original(name, expected)

    monkeypatch.setattr(recipe.sources, "checked", changed)
    with pytest.raises(ValueError, match="injected_digest_mismatch"):
        recipe.derive(OBSERVATION, OBSERVATION_SHA)


@pytest.mark.parametrize("field,value", [
    ("decision", "REJECTED"), ("blocking_findings", ["synthetic blocker"]),
    ("operations_authorized", True),
])
def test_synthetic_baseline_review_must_be_accepted_without_operation_grant(monkeypatch, field, value):
    original = recipe.sources.checked

    def altered(name, expected):
        raw = original(name, expected)
        if name == recipe.BASELINE_REVIEW:
            data = json.loads(raw)
            data[field] = value
            return recipe.install.canonical(data)
        return raw

    monkeypatch.setattr(recipe.sources, "checked", altered)
    with pytest.raises(ValueError, match="baseline_not_reviewed"):
        recipe.derive(OBSERVATION, OBSERVATION_SHA)


@pytest.mark.parametrize("different_path", [False, True])
def test_unreviewed_receipt_or_path_refuses(tmp_path, different_path):
    path = tmp_path / "not_the_reviewed_receipt.json" if different_path else OBSERVATION
    sha = OBSERVATION_SHA if different_path else "0" * 64
    with pytest.raises(ValueError, match="observation_not_reviewed"):
        recipe.derive(path, sha)
