"""Real-loader composition under synthetic reviews only; no native work."""
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.research import companion_cutover as entry, companion_runtime_adapter as adapter
from tests.test_companion_runtime_adapter import seal_fixture_reviews
from tests.test_companion_archive_contract import ROOT, offline

BASE = ROOT / "docs/review_artifacts/companion_reconnection_plan_20261024"
spec = importlib.util.spec_from_file_location("v6e_packet", BASE / "assemble_runtime_packet_v6e.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    offline(monkeypatch)
    def forbidden(*a, **k):
        raise AssertionError("packet attempted native/reservation operation")
    monkeypatch.setattr(entry, "DockerInstallBackend", forbidden)
    monkeypatch.setattr(entry, "_reserve", forbidden)


def test_exact_subjects_sources_and_new_evidence_contract():
    out = recipe.derive()
    prior = json.loads(recipe.raw_checked(*recipe.PINS["prior_runtime"]))
    actual = json.loads(recipe.raw_checked(*recipe.PINS["evidence"]))
    subjects = out["subjects.draft.json"]
    assert subjects[:3] == prior["subjects"][:3]
    for before, now, row in zip(prior["subjects"][3:], subjects[3:], actual["replacements"]):
        assert now["container_id"] == row["id"] != before["container_id"]
        assert now["image_id"] == before["image_id"] and now["sources"] == before["sources"]
    proof = out["provenance.json"]
    assert proof["total_source_pins"] == 132
    assert len(proof["consumer_sha256"]) == 20 and len(proof["preparation_consumer_sha256"]) == 13
    assert [r["document_id"] for r in out["topical_approvals.json"]] == [7, 5, 47, 18]
    for name, value in out.items():
        if name.endswith(".draft.json") and name != "subjects.draft.json":
            assert value["decision"] == "INCOMPLETE" and value["reviewer"] == ""
            assert set(value.get("policies", {}).values()) <= {"UNVERIFIED"}


def test_actual_loader_accepts_composition_with_synthetic_reviews_only(tmp_path):
    out = recipe.derive()
    subjects = out["subjects.draft.json"]
    pins = adapter.ReviewedPins(tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"],
        s["preservation_sha256"], tuple(sorted(s["sources"].items()))) for s in subjects),
        "0" * 64, (), tuple(out["topical_approvals.json"]), b"", ())
    pins = seal_fixture_reviews(pins)
    runtime = json.loads(pins.review_manifest)
    runtime.update(schema="companion-runtime-pins-v2", network_configuration=out["runtime_review.draft.json"]["network_configuration"])
    raw = adapter._canonical(runtime)
    pins = replace(pins, review_manifest=raw, review_record_sha256=hashlib.sha256(raw).hexdigest())
    for name in ("staged_metadata.derived.json", "topical_approvals.json"):
        (tmp_path / name).write_bytes(adapter._canonical(out[name]))
    (tmp_path / "runtime.json").write_bytes(raw)
    children = []
    for index, value in enumerate(pins.dependency_review_records):
        p = tmp_path / f"synthetic-{index}.json";p.write_bytes(value);children.append(p)
    args = SimpleNamespace(manifest=ROOT / recipe.PINS["manifest"][0], reviewed_manifest_sha256=recipe.PINS["manifest"][1],
        preparation_evidence=ROOT / recipe.PINS["evidence"][0], preparation_review=ROOT / recipe.PINS["id_review"][0],
        reviewed_preparation_review_sha256=recipe.PINS["id_review"][1], staged_metadata=tmp_path / "staged_metadata.derived.json",
        runtime_review=tmp_path / "runtime.json", reviewed_runtime_review_sha256=pins.review_record_sha256,
        topical_approvals=tmp_path / "topical_approvals.json", dependency_review=children)
    plan, prepared, loaded = entry.load_inputs(args)
    assert loaded == pins and len(prepared.replacements) == 4 and plan.attempt == "workerprep20261024v6e"


@pytest.mark.parametrize("key", ["id_review", "actual_review", "correction", "prior_scope", "topical"])
def test_changed_input_binding_refuses(monkeypatch, key):
    path, _ = recipe.PINS[key]
    monkeypatch.setitem(recipe.PINS, key, (path, "0" * 64))
    with pytest.raises(ValueError, match="input_changed"):
        recipe.derive()


def test_client_guard_drift_refuses(monkeypatch):
    monkeypatch.setitem(recipe.CLIENTS, "dashboard/services/views/_shared_signals.py", "0" * 64)
    with pytest.raises(ValueError, match="input_changed"):
        recipe.derive()


@pytest.mark.parametrize("change", ["witness_id", "witness_hash", "duplicate", "stage_alias", "image", "original", "prior_child"])
def test_saved_evidence_contradictions_refuse(monkeypatch, change):
    original = recipe.checked
    def altered(path, sha):
        raw = original(path, sha)
        if path == recipe.PINS["postcheck"][0] and change != "prior_child":
            value = json.loads(raw)
            if change == "duplicate":
                value["source_files"][1] = value["source_files"][0]
            elif change == "original":
                value["before"][0]["image"] = "sha256:" + "f" * 64
                value["after"] = value["before"]
            elif change in {"stage_alias", "image"}:
                if change == "image":
                    value["rows"][0]["image"] = "sha256:" + "f" * 64
                else:
                    next(iter(value["rows"][0]["networks"].values()))["Aliases"] = ["unexpected"]
            else:
                value["source_files"][0]["container_id" if change == "witness_id" else "sha256"] = "f" * 64
            return adapter._canonical(value)
        if "/accepted_policy_records/phase1-" in path and change == "prior_child":
            value = json.loads(raw);value["subjects"] = []
            return adapter._canonical(value)
        return raw
    monkeypatch.setattr(recipe, "checked", altered)
    with pytest.raises(ValueError):
        recipe.derive()
