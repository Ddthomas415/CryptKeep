"""Frozen fresh-baseline proposal; no native/process/credential operations."""
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
spec = importlib.util.spec_from_file_location("fresh_preparation", BASE / "derive_fresh_preparation.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("proposal attempted native/network work")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def test_exact_allowed_delta_and_no_approval():
    candidate, proof = recipe.derive()
    previous = json.loads((BASE / recipe.PINS["manifest"][0]).read_bytes())
    assert {key for key in previous if previous[key] != candidate[key]} == {"attempt", "decision", "reviewer", "baseline"}
    assert candidate["applications"] == previous["applications"]
    assert proof["applications_unchanged"] and proof["new_container_ids"] is None
    assert not proof["preparation_authorized"] and not proof["cutover_authorized"]
    with pytest.raises(install.core.Refused):
        install.Plan.load(install.canonical(candidate), proof["candidate_sha256"])
    # In-memory fixture approval only, never an executable artifact.
    approved = {**candidate, "decision": "ACCEPTED_WITH_RISK", "reviewer": "SYNTHETIC_ONLY"}
    raw = install.canonical(approved)
    plan = install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    assert plan.staged and plan.worker_shutdown and plan.attempt == recipe.ATTEMPT


@pytest.mark.parametrize("change", ["id", "image", "running", "config", "restarts", "final", "cli"])
def test_fresh_capture_drift_refuses(monkeypatch, change):
    original = recipe.checked
    def altered(path, expected):
        raw = original(path, expected)
        if path == BASE / recipe.PINS["observation"][0]:
            value = json.loads(raw)
            row = value["observations"][3]
            if change in {"id", "image"}:
                row[change] = ("sha256:" if change == "image" else "") + "f" * 64
            elif change == "running":
                row["state"] = "exited"
            elif change == "config":
                row["command"] = ["different"]
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
    monkeypatch.setattr(recipe, "checked", altered)
    with pytest.raises(ValueError):
        recipe.derive()


def test_consumed_attempt_and_input_hash_refuse(monkeypatch):
    monkeypatch.setattr(recipe.os.path, "lexists", lambda p: True)
    with pytest.raises(ValueError, match="attempt_consumed"):
        recipe.derive()
    monkeypatch.setattr(recipe.os.path, "lexists", lambda p: False)
    name, _ = recipe.PINS["observation"]
    monkeypatch.setitem(recipe.PINS, "observation", (name, "f" * 64))
    with pytest.raises(ValueError, match="input_changed"):
        recipe.derive()
