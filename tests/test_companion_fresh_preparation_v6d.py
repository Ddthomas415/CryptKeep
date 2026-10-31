"""Offline new-attempt proposal; original recipe and consumed records untouched."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess

import pytest

from scripts.research import companion_installer as install

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/review_artifacts/companion_worker_preparation_20261023"
spec = importlib.util.spec_from_file_location("v6d_proposal", BASE / "derive_fresh_preparation_v6d.py")
proposal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proposal)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("proposal attempted process/network access")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def test_exact_new_attempt_delta_not_an_approval():
    candidate, proof = proposal.derive()
    old = json.loads((BASE / proposal.PINS["manifest"][0]).read_bytes())
    assert {k for k in old if old[k] != candidate[k]} == {"attempt", "decision", "reviewer", "baseline"}
    assert candidate["attempt"] != old["attempt"]
    assert candidate["applications"] == old["applications"]
    assert candidate["policies"] == old["policies"]
    assert len(proof["consumer_sha256"]) == 13
    assert proof["new_container_ids"] is None and proof["new_image_ids"] is None
    assert not proof["preparation_authorized"] and not proof["startup_authorized"]
    with pytest.raises(install.core.Refused):
        install.Plan.load(install.canonical(candidate), proof["candidate_sha256"])
    fixture = {**candidate, "decision": "ACCEPTED_WITH_RISK", "reviewer": "SYNTHETIC_ONLY"}
    raw = install.canonical(fixture)
    plan = install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    assert plan.staged and plan.worker_shutdown and plan.attempt == proposal.ATTEMPT


@pytest.mark.parametrize("change", ["id", "image", "state", "config", "restarts", "final", "cli"])
def test_fresh_baseline_drift_refuses(monkeypatch, change):
    worker = proposal.recipe()
    original = worker.checked
    def altered(path, sha):
        raw = original(path, sha)
        if path == BASE / proposal.PINS["observation"][0]:
            value = json.loads(raw)
            row = value["observations"][3]
            if change in {"id", "image"}:
                row[change] = ("sha256:" if change == "image" else "") + "f" * 64
            elif change == "state":
                row["state"] = "exited"
            elif change == "config":
                row["command"] = ["changed"]
            elif change == "restarts":
                row["restarts"] += 1
            elif change == "cli":
                value["cli_sha256"] = "f" * 64
            else:
                value["final_observations_match"] = False
            if change != "final":
                value["final_observations"] = deepcopy(value["observations"])
            return install.canonical(value)
        return raw
    monkeypatch.setattr(worker, "checked", altered)
    monkeypatch.setattr(proposal, "recipe", lambda: worker)
    with pytest.raises(ValueError):
        proposal.derive()


def test_consumed_marker_and_helper_drift_refuse(monkeypatch):
    factory = proposal.recipe
    worker = factory()
    monkeypatch.setattr(worker.os.path, "lexists", lambda path: True)
    monkeypatch.setattr(proposal, "recipe", lambda: worker)
    with pytest.raises(ValueError, match="attempt_consumed"):
        proposal.derive()
    monkeypatch.setattr(proposal, "recipe", factory)
    monkeypatch.setattr(proposal, "HELPER_SHA", "f" * 64)
    with pytest.raises(ValueError, match="input_changed"):
        proposal.recipe()
