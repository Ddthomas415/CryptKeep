"""Offline source-refresh and baseline contract; all new baselines are fixtures."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from scripts.research import companion_installer as install
from tests.test_companion_archive_contract import ROOT, offline

BASE = ROOT / "docs/review_artifacts/companion_integration_inputs_v6f_20261025"
spec = importlib.util.spec_from_file_location("integration_inputs_v6f", BASE / "derive_inputs.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def no_operations(monkeypatch):
    offline(monkeypatch)


@pytest.fixture
def observation(tmp_path):
    # Prior paired capture is used only to construct synthetic current-start fixtures.
    p = ROOT / "docs/review_artifacts/companion_runtime_inventory_20261024/observation.json"
    raw = recipe.checked(p, "0a71483b1ee7e54874975647d0105b3f03bc44a9c2274e8a5350ed34bc950793")
    value = json.loads(raw)
    for row in value["observations"][0][3:]:
        row["started"] = "2026-10-25T06:00:00Z"
    value["observations"][1] = deepcopy(value["observations"][0])
    value["observed_end_utc"] = "2026-10-25T06:01:00+00:00"
    return tmp_path / "synthetic_baseline.json", value


def propose(observation):
    p, value = observation
    raw = install.canonical(value)
    p.write_bytes(raw)
    return recipe.derive(p, hashlib.sha256(raw).hexdigest())


def test_exact_reviewed_source_and_consumer_delta_only(observation):
    assert all("attempt" not in row for row in observation[1]["observations"][0])
    candidate, proof = propose(observation)
    old = json.loads(recipe.checked(ROOT / recipe.PINS["manifest"][0], recipe.PINS["manifest"][1]))
    assert {k for k in old if old[k] != candidate[k]} == {"attempt", "decision", "reviewer", "baseline", "applications"}
    assert candidate["attempt"] == "workerprep20261025v6f" and candidate["decision"] == "INCOMPLETE"
    assert candidate["reviewer"] == "" and candidate["policies"] == old["policies"]
    for before, now in zip(old["applications"], candidate["applications"]):
        assert {k:v for k,v in before.items() if k != "sources"} == {k:v for k,v in now.items() if k != "sources"}
        assert [(s["local"], s["destination"]) for s in before["sources"]] == [(s["local"], s["destination"]) for s in now["sources"]]
    assert {d["path"] for d in proof["source_deltas"]} == recipe.CHANGED
    assert len(proof["source_deltas"]) == 3 and len(proof["consumer_sha256"]) == 13
    assert sum(len(a["sources"]) for a in candidate["applications"]) == 43
    assert proof["new_container_ids"] is None and proof["new_image_ids"] is None
    assert proof["prediction_evidence"] == "MODELLED"
    assert not proof["preparation_authorized"] and not proof["cutover_authorized"]
    with pytest.raises(install.core.Refused):
        install.Plan.load(install.canonical(candidate), proof["candidate_sha256"])
    fixture = {**candidate, "decision":"ACCEPTED_WITH_RISK", "reviewer":"SYNTHETIC_ONLY"}
    raw = install.canonical(fixture)
    assert install.Plan.load(raw, hashlib.sha256(raw).hexdigest()).worker_shutdown


@pytest.mark.parametrize("change", ["id", "image", "state", "command", "restarts", "pair", "cli", "complete"])
def test_baseline_drift_refuses(observation, change):
    _, value = observation
    row = value["observations"][0][3]
    if change in {"id", "image"}:
        row[change] = ("sha256:" if change == "image" else "") + "f" * 64
    elif change == "state": row[change] = "exited"
    elif change == "command": row[change] = ["changed"]
    elif change == "restarts": row[change] += 1
    elif change == "cli": value["cli_sha256"] = "f" * 64
    elif change == "complete": value["metadata_complete_for_selected_fields"] = False
    if change != "pair":
        value["observations"][1] = deepcopy(value["observations"][0])
    else:
        value["observations"][1][3]["started"] = "2026-10-25T06:00:01Z"
    with pytest.raises(ValueError):
        propose(observation)


@pytest.mark.parametrize("path", sorted(recipe.CHANGED))
def test_repaired_source_drift_refuses(monkeypatch, path):
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"changed" if p == ROOT / path else read(p))
    with pytest.raises(ValueError, match="input_changed"):
        recipe.source_inputs()


def test_changed_review_or_consumed_new_label_refuses(observation, monkeypatch):
    path, digest = recipe.PINS["review"]
    monkeypatch.setitem(recipe.PINS, "review", (path, "0" * 64))
    with pytest.raises(ValueError, match="input_changed"):
        recipe.source_inputs()
    monkeypatch.setitem(recipe.PINS, "review", (path, digest))
    original = recipe.os.path.lexists
    monkeypatch.setattr(recipe.os.path, "lexists", lambda p: True if str(p).endswith(recipe.ATTEMPT) else original(p))
    with pytest.raises(ValueError, match="attempt_consumed"):
        propose(observation)
