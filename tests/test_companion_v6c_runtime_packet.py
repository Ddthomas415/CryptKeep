"""V6c packet and real-loader composition; no native work or actual approvals."""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace

import pytest

from scripts.research import companion_cutover as entry
from scripts.research import companion_runtime_adapter as adapter
from tests.test_companion_runtime_adapter import seal_fixture_reviews

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "docs/review_artifacts/companion_worker_preparation_20261023"
spec = importlib.util.spec_from_file_location("v6c_packet", HERE / "assemble_runtime_packet_v6c.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("offline V6c packet attempted native/network/reservation work")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(entry, "DockerInstallBackend", forbidden)
    monkeypatch.setattr(entry, "_reserve", forbidden)


def test_exact_sources_storage_and_new_id_scope():
    out = recipe.derive()
    prior = json.loads((ROOT / recipe.PINS["prior_runtime"][0]).read_bytes())
    actual = json.loads((ROOT / recipe.PINS["evidence"][0]).read_bytes())
    subjects = out["subjects.draft.json"]
    assert subjects[:3] == prior["subjects"][:3]
    for before, after, prepared in zip(prior["subjects"][3:], subjects[3:], actual["replacements"]):
        assert before["sources"] == after["sources"] and before["image_id"] == after["image_id"]
        assert after["container_id"] == prepared["id"] != before["container_id"]
    proof = out["provenance.json"]
    assert proof["total_source_pins"] == 132
    assert proof["direct_application_source_witnesses"] + proof["inherited_same_image_or_storage_pins"] == 132
    assert all(not proof[k] for k in ("native_operations", "credential_access", "policy_approval_created", "cutover_authorized"))
    for name, value in out.items():
        if name.endswith(".draft.json") and name != "subjects.draft.json":
            assert value["decision"] == "INCOMPLETE" and value["reviewer"] == ""
            assert set(value.get("policies", {}).values()) <= {"UNVERIFIED"}


def test_generated_packet_reproduces_exact_bytes():
    for name, value in recipe.derive().items():
        assert (HERE / "runtime_packet_v6c" / name).read_bytes() == recipe.install.canonical(value)


def test_real_loader_accepts_v2_composition_with_synthetic_reviews_only(tmp_path):
    out = recipe.derive()
    subjects = out["subjects.draft.json"]
    pins = adapter.ReviewedPins(tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"],
        s["preservation_sha256"], tuple(sorted(s["sources"].items()))) for s in subjects), "0" * 64, (),
        tuple(out["topical_approvals.json"]), b"", ())
    pins = seal_fixture_reviews(pins)
    runtime = json.loads(pins.review_manifest)
    runtime.update(schema="companion-runtime-pins-v2", network_configuration=out["runtime_review.draft.json"]["network_configuration"])
    raw = recipe.install.canonical(runtime)
    pins = replace(pins, review_manifest=raw, review_record_sha256=recipe.digest(raw))
    for name in ("staged_metadata.derived.json", "topical_approvals.json"):
        (tmp_path / name).write_bytes(recipe.install.canonical(out[name]))
    (tmp_path / "runtime.json").write_bytes(raw)
    children = []
    for index, child in enumerate(pins.dependency_review_records):
        path = tmp_path / f"synthetic-{index}.json"
        path.write_bytes(child)
        children.append(path)
    args = SimpleNamespace(manifest=ROOT / recipe.PINS["manifest"][0], reviewed_manifest_sha256=recipe.PINS["manifest"][1],
        preparation_evidence=ROOT / recipe.PINS["evidence"][0], preparation_review=ROOT / recipe.PINS["id_review"][0],
        reviewed_preparation_review_sha256=recipe.PINS["id_review"][1], staged_metadata=tmp_path / "staged_metadata.derived.json",
        runtime_review=tmp_path / "runtime.json", reviewed_runtime_review_sha256=pins.review_record_sha256,
        topical_approvals=tmp_path / "topical_approvals.json", dependency_review=children)
    plan, prepared, loaded = entry.load_inputs(args)
    assert loaded == pins and len(prepared.replacements) == 4 and plan.attempt == "workerprep20261023v6c"


@pytest.mark.parametrize("key", ["id_review", "actual_review", "correction", "prior_scope"])
def test_changed_review_binding_refuses(monkeypatch, key):
    path, _ = recipe.PINS[key]
    monkeypatch.setitem(recipe.PINS, key, (path, "0" * 64))
    with pytest.raises(ValueError, match="input_changed"):
        recipe.derive()


@pytest.mark.parametrize("change", ["witness_id", "witness_hash", "duplicate", "stage_alias", "image", "original", "prior_child"])
def test_saved_evidence_contradictions_refuse(monkeypatch, change):
    original = recipe.checked
    def altered(path, sha):
        raw = original(path, sha)
        if path == recipe.PINS["postcheck"][0] and change in {"witness_id", "witness_hash", "duplicate", "original"}:
            value = json.loads(raw)
            if change == "duplicate":
                value["source_files"][1] = value["source_files"][0]
            elif change == "original":
                value["before"][0]["image"] = "sha256:" + "f" * 64
                value["after"] = value["before"]
            else:
                value["source_files"][0]["container_id" if change == "witness_id" else "sha256"] = "f" * 64
            return recipe.install.canonical(value)
        if path == recipe.PINS["metadata"][0] and change in {"stage_alias", "image"}:
            value = json.loads(raw)
            if change == "image":
                value["rows"][0]["image"] = "sha256:" + "f" * 64
            else:
                next(iter(value["rows"][0]["networks"].values()))["Aliases"] = ["unexpected"]
            return recipe.install.canonical(value)
        if "/accepted_policy_records/phase1-" in path and change == "prior_child":
            value = json.loads(raw)
            value["subjects"] = []
            return recipe.install.canonical(value)
        return raw
    monkeypatch.setattr(recipe, "checked", altered)
    with pytest.raises(ValueError):
        recipe.derive()
