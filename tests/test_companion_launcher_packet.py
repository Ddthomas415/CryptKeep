"""Exact additive launcher pins; native operations forbidden."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import socket
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "docs/review_artifacts/companion_worker_preparation_20261023"
spec = importlib.util.spec_from_file_location("launcher_packet", HERE / "derive_launcher_packet.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline packet attempted native/network access")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def prior_subjects():
    return json.loads((HERE / "runtime_packet_v6b/subjects.draft.json").read_bytes())


def test_exact_additive_four_pins_preserves_every_prior_field():
    out = recipe.derive()
    previous = prior_subjects()
    recipe.validate_subjects(out["subjects.draft.json"], previous)
    restored = deepcopy(out["subjects.draft.json"])
    for subject in restored[3:]:
        assert subject["sources"].pop(recipe.SOURCE) == recipe.SOURCE_SHA
    assert restored == previous
    assert out["provenance.json"]["total_source_pins"] == 132


@pytest.mark.parametrize("change", ["missing", "wrong_hash", "wrong_id", "extra_source"])
def test_required_launcher_pins_cannot_be_omitted_or_changed(change):
    previous = prior_subjects()
    subjects = recipe.derive()["subjects.draft.json"]
    if change == "missing":
        del subjects[3]["sources"][recipe.SOURCE]
    elif change == "wrong_hash":
        subjects[3]["sources"][recipe.SOURCE] = "0" * 64
    elif change == "wrong_id":
        subjects[3]["container_id"] = "0" * 64
    else:
        subjects[3]["sources"]["/app/extra.py"] = "0" * 64
    with pytest.raises(ValueError, match="launcher_pin_missing_or_changed"):
        recipe.validate_subjects(subjects, previous)


def test_changed_capture_review_refuses(monkeypatch):
    path, _ = recipe.PINS["capture_review"]
    monkeypatch.setitem(recipe.PINS, "capture_review", (path, "0" * 64))
    with pytest.raises(ValueError, match="launcher_packet_input_changed"):
        recipe.derive()


def test_changed_consumer_refuses(monkeypatch):
    monkeypatch.setattr(recipe, "NEW_TRANSPORT", "0" * 64)
    with pytest.raises(ValueError, match="launcher_packet_input_changed"):
        recipe.derive()


def test_no_policy_or_operational_approval_and_output_reproducible():
    for name, value in recipe.derive().items():
        assert (HERE / "runtime_packet_v6b_launcher" / name).read_bytes() == recipe.install.canonical(value)
        if name.endswith(".draft.json") and name != "subjects.draft.json":
            assert value["decision"] == "INCOMPLETE" and value["reviewer"] == ""
            assert set(value.get("policies", {}).values()) <= {"UNVERIFIED"}
    proof = recipe.derive()["provenance.json"]
    assert all(not proof[k] for k in ("native_operations", "credential_access", "cutover_authorized", "policy_approval_created"))
