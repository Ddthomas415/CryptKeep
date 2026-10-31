"""Saved-pair derivation and synthetic drift; no daemon or lifecycle calls."""
from copy import deepcopy
import hashlib
import importlib
import json

import pytest

from tests.test_companion_archive_contract import offline


recipe = importlib.import_module(
    "docs.review_artifacts.companion_integration_inputs_v6h_20261026.derive_inputs")
OBSERVATION = recipe.HERE / "actual_baseline/baseline_observation.json"
OBSERVATION_SHA = "685af8cea00eec5d7026afbf585d7e588620e0c69eb70a56a3393decf443d129"


@pytest.fixture(autouse=True)
def no_operations(monkeypatch):
    offline(monkeypatch)


def test_actual_saved_inputs_reproduce_and_remain_unapproved():
    candidate, proof = recipe.derive(OBSERVATION, OBSERVATION_SHA)
    assert recipe.install.canonical(candidate) == (recipe.HERE / "candidate_manifest.json").read_bytes()
    assert recipe.install.canonical(proof) == (recipe.HERE / "provenance.json").read_bytes()
    assert [r["changed_fields"] for r in proof["baseline_deltas"]] == [[]] * 3 + [["started"]] * 4
    assert candidate["decision"] == "INCOMPLETE" and candidate["reviewer"] == ""
    raw = recipe.install.canonical(candidate)
    with pytest.raises(recipe.install.core.Refused):
        recipe.install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    fixture = deepcopy(candidate)
    fixture.update(decision="ACCEPTED_WITH_RISK", reviewer="SYNTHETIC_ONLY")
    raw = recipe.install.canonical(fixture)
    assert recipe.install.Plan.load(raw, hashlib.sha256(raw).hexdigest()).worker_shutdown


@pytest.mark.parametrize("change", ["id", "state", "command", "restarts", "storage_started",
                                    "cli", "pair", "raw_hash", "deadline", "source_refresh"])
def test_synthetic_baseline_drift_refuses(tmp_path, change):
    observed = json.loads(OBSERVATION.read_text())
    row = observed["observations"][0][3]
    if change == "id":
        row["id"] = "f" * 64
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
    if change != "pair":
        observed["observations"][1] = deepcopy(observed["observations"][0])
    else:
        observed["observations"][1][3]["started"] = "2026-10-26T00:00:01Z"
    for index, rows in enumerate(observed["observations"], 1):
        raw = b"".join(json.dumps(r).encode() + b"\n" for r in rows)
        (tmp_path / f"capture_{index}.jsonl").write_bytes(raw)
        observed["raw_sha256"][index - 1] = hashlib.sha256(raw).hexdigest()
    if change == "raw_hash":
        observed["raw_sha256"][0] = "0" * 64
    raw = recipe.install.canonical(observed)
    path = tmp_path / "synthetic_observation.json"
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        recipe.derive(path, hashlib.sha256(raw).hexdigest())
