"""Pure, offline checks of the exact-ID packet proposal, not runtime behavior."""
import importlib.util
import json
from pathlib import Path
import socket
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "docs/review_artifacts/companion_worker_preparation_20261023"
spec = importlib.util.spec_from_file_location("v6b_runtime_packet", HERE / "assemble_runtime_packet.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("packet derivation attempted native/network work")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def test_exact_subjects_preserve_sources_images_and_storage():
    artifacts = recipe.derive()
    previous = json.loads((ROOT / recipe.PINS["prior_runtime"][0]).read_bytes())["subjects"]
    subjects = artifacts["subjects.draft.json"]
    assert subjects[:3] == previous[:3]
    for old, new in zip(previous[3:], subjects[3:]):
        assert old["image_id"] == new["image_id"] and old["sources"] == new["sources"]
        assert old["container_id"] != new["container_id"]
    assert sum(len(s["sources"]) for s in subjects) == 128


def test_no_acceptance_or_runtime_authority_is_created():
    artifacts = recipe.derive()
    for name, value in artifacts.items():
        if name.endswith(".draft.json") and name != "subjects.draft.json":
            assert value["decision"] == "INCOMPLETE" and value["reviewer"] == ""
            assert set(value.get("policies", {}).values()) <= {"UNVERIFIED"}
    proof = artifacts["provenance.json"]
    assert proof["runtime_state"] == "INCOMPLETE" and proof["direct_application_source_witnesses"] == 43
    assert all(not proof[k] for k in ("native_operations", "credential_access", "cutover_authorized", "policy_approval_created"))
    assert all(d["final_configuration_evidence"] == "MODELLED" for d in proof["subject_delta"])


def test_binding_hash_change_refuses(monkeypatch):
    path, _ = recipe.PINS["metadata"]
    monkeypatch.setitem(recipe.PINS, "metadata", (path, "0" * 64))
    with pytest.raises(ValueError, match="packet_input_changed"):
        recipe.derive()


def test_consumer_change_refuses(monkeypatch):
    monkeypatch.setattr(recipe, "CUTOVER_SHA", "0" * 64)
    with pytest.raises(ValueError, match="packet_input_changed"):
        recipe.derive()


@pytest.mark.parametrize("field,value", [("sha256", "0" * 64), ("container_id", "0" * 64)])
def test_wrong_direct_source_witness_refuses(monkeypatch, field, value):
    original = recipe.checked
    def altered(path, expected):
        raw = original(path, expected)
        if path == recipe.PINS["sources"][0]:
            payload = json.loads(raw)
            payload["source_files"][0][field] = value
            return recipe.install.canonical(payload)
        return raw
    monkeypatch.setattr(recipe, "checked", altered)
    with pytest.raises(ValueError, match="source_witness_changed"):
        recipe.derive()


def test_published_artifacts_are_reproducible():
    for name, value in recipe.derive().items():
        assert (HERE / "runtime_packet_v6b" / name).read_bytes() == recipe.install.canonical(value)
