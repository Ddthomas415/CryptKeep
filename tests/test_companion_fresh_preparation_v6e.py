"""Fresh offline preparation inputs; old recipes, packets and markers preserved."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from scripts.research import companion_installer as install
from tests.test_companion_archive_contract import ROOT, offline

PATH = ROOT / "docs/review_artifacts/companion_reconnection_plan_20261024/derive_preparation_inputs.py"
spec = importlib.util.spec_from_file_location("offline_inputs_v6e", PATH)
proposal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proposal)


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    offline(monkeypatch)


def test_new_inputs_change_only_label_review_fields_and_baseline():
    candidate, proof = proposal.derive()
    old = json.loads(proposal.read_checked(ROOT / proposal.PINS["manifest"][0], proposal.PINS["manifest"][1]))
    assert {k for k in old if old[k] != candidate[k]} == {"attempt", "decision", "reviewer", "baseline"}
    assert candidate["attempt"] == "workerprep20261024v6e"
    assert candidate["applications"] == old["applications"] and candidate["policies"] == old["policies"]
    assert len(proof["consumer_sha256"]) == 13
    assert proof["new_container_ids"] is None and proof["new_image_ids"] is None
    assert not proof["preparation_authorized"] and not proof["startup_authorized"]
    with pytest.raises(install.core.Refused):
        install.Plan.load(install.canonical(candidate), proof["candidate_sha256"])
    fixture = {**candidate, "decision": "ACCEPTED_WITH_RISK", "reviewer": "SYNTHETIC_ONLY"}
    raw = install.canonical(fixture)
    assert install.Plan.load(raw, hashlib.sha256(raw).hexdigest()).staged


def test_schema_adapter_is_bound_and_source_capture_unchanged():
    path, sha = proposal.PINS["observation"]
    original = proposal.read_checked(ROOT / path, sha)
    saved = json.loads(original)
    adapted = json.loads(proposal.checked(ROOT / path, sha))
    assert adapted["observations"] == saved["observations"][0]
    assert adapted["final_observations"] == saved["observations"][1]
    assert adapted["observed_utc"] == saved["observed_end_utc"]
    assert (ROOT / path).read_bytes() == original


@pytest.mark.parametrize("change", ["id", "image", "state", "command", "restarts"])
def test_baseline_drift_fails_existing_recipe_checks(change):
    worker = proposal.recipe()
    original = worker.checked
    def altered(path, sha):
        raw = original(path, sha)
        if path == ROOT / proposal.PINS["observation"][0]:
            value = json.loads(raw)
            row = value["observations"][3]
            row[change] = {"id": "f" * 64, "image": "sha256:" + "f" * 64,
                           "state": "exited", "command": ["altered"], "restarts": 1}[change]
            value["final_observations"] = deepcopy(value["observations"])
            return install.canonical(value)
        return raw
    worker.checked = altered
    with pytest.raises(ValueError):
        worker.derive()


def test_new_label_consumed_or_helper_drift_refuses(monkeypatch):
    original = proposal.os.path.lexists
    monkeypatch.setattr(proposal.os.path, "lexists", lambda p: True if str(p).endswith(proposal.ATTEMPT) else original(p))
    with pytest.raises(ValueError, match="attempt_consumed"):
        proposal.derive()
    monkeypatch.setattr(proposal, "HELPER_SHA", "0" * 64)
    with pytest.raises(ValueError, match="fresh_input_changed"):
        proposal.recipe()
