"""Offline V6g composition; model rows and synthetic approvals are explicit."""
from dataclasses import replace
import importlib
import json
from types import SimpleNamespace

import pytest

from scripts.research import companion_cutover as entry
from tests.test_companion_archive_contract import ROOT, offline
from tests.test_companion_runtime_adapter import seal_fixture_reviews


recipe = importlib.import_module(
    "docs.review_artifacts.companion_integration_inputs_v6g_20261025.assemble_runtime_packet")


@pytest.fixture(autouse=True)
def no_operations(monkeypatch):
    offline(monkeypatch)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("packet attempted native/token/reservation work")

    monkeypatch.setattr(entry, "DockerInstallBackend", forbidden)
    monkeypatch.setattr(entry, "_reserve", forbidden)
    monkeypatch.setattr(recipe.adapter, "token_from_pipe", forbidden)


def test_exact_actual_ids_same_images_and_historical_pin_basis():
    artifacts = recipe.derive()
    previous = json.loads(recipe.checked(*recipe.PINS["prior_runtime"]))
    subjects, proof = artifacts["subjects.draft.json"], artifacts["provenance.json"]
    assert subjects[:3] == previous["subjects"][:3] and len(artifacts) == 12
    for before, now in zip(previous["subjects"][3:], subjects[3:]):
        assert now["container_id"] != before["container_id"]
        assert now["image_id"] == before["image_id"] and now["sources"] == before["sources"]
    assert proof["total_source_pins"] == 132
    assert proof["direct_file_streams_recaptured"] == 0
    assert proof["application_entries_controller_attested"] == 43
    assert proof["inherited_exact_prior_image_or_storage_pins"] == 89
    assert proof["historical_pin_basis"] == {"prior_exact_image_or_storage": 52, "prior_common_parent_memory_library": 37}
    assert artifacts["staged_metadata.derived.json"]["raw_v6g_capture"] is False
    assert artifacts["staged_metadata.derived.json"]["evidence_lane"].startswith("MODELLED")
    assert [a["document_id"] for a in artifacts["topical_approvals.json"]] == [7, 5, 47, 18]
    scope = json.loads(recipe.checked(*recipe.PINS["prior_scope"]))
    assert proof["preserved_policy_meanings"] == scope["policy_meanings"]
    assert proof["preserved_limits"] == scope["preserved_limits"]
    assert {p for p, h in proof["consumer_sha256"].items() if h != scope["consumer_sha256"][p]} == {recipe.GUARD}
    for name, value in artifacts.items():
        if name.endswith(".draft.json") and name != "subjects.draft.json":
            assert value["decision"] == "INCOMPLETE" and value["reviewer"] == ""
            assert set(value.get("policies", {}).values()) <= {"UNVERIFIED"}


def test_real_loader_composes_with_temporary_synthetic_reviews(tmp_path):
    artifacts = recipe.derive()
    subjects = artifacts["subjects.draft.json"]
    adapter = recipe.adapter
    pins = adapter.ReviewedPins(tuple(adapter.TargetPin(s["name"], s["container_id"], s["image_id"],
        s["preservation_sha256"], tuple(sorted(s["sources"].items()))) for s in subjects),
        "0" * 64, (), tuple(artifacts["topical_approvals.json"]), b"", ())
    pins = seal_fixture_reviews(pins)
    runtime = json.loads(pins.review_manifest)
    runtime.update(schema="companion-runtime-pins-v2",
                   network_configuration=artifacts["runtime_review.draft.json"]["network_configuration"])
    raw = adapter._canonical(runtime)
    pins = replace(pins, review_manifest=raw, review_record_sha256=recipe.digest(raw))
    for name in ("staged_metadata.derived.json", "topical_approvals.json"):
        (tmp_path / name).write_bytes(adapter._canonical(artifacts[name]))
    (tmp_path / "runtime.json").write_bytes(raw)
    children = []
    for number, child in enumerate(pins.dependency_review_records):
        path = tmp_path / f"synthetic-{number}.json"
        path.write_bytes(child)
        children.append(path)
    args = SimpleNamespace(manifest=ROOT / recipe.PINS["manifest"][0],
        reviewed_manifest_sha256=recipe.PINS["manifest"][1],
        preparation_evidence=ROOT / recipe.PINS["evidence"][0],
        preparation_review=ROOT / recipe.PINS["id_review"][0],
        reviewed_preparation_review_sha256=recipe.PINS["id_review"][1],
        staged_metadata=tmp_path / "staged_metadata.derived.json", runtime_review=tmp_path / "runtime.json",
        reviewed_runtime_review_sha256=pins.review_record_sha256,
        topical_approvals=tmp_path / "topical_approvals.json", dependency_review=children)
    plan, prepared, loaded = entry.load_inputs(args)
    assert loaded == pins and plan.attempt == "workerprep20261025v6g"
    assert len(prepared.replacements) == 4


@pytest.mark.parametrize("key", sorted(recipe.PINS))
def test_fixed_input_drift_refuses(monkeypatch, key):
    path, _ = recipe.PINS[key]
    monkeypatch.setitem(recipe.PINS, key, (path, "0" * 64))
    with pytest.raises(ValueError, match="input_changed"):
        recipe.derive()


@pytest.mark.parametrize("change", ["consumer", "identity_review", "command", "alias", "image", "library", "historical_basis"])
def test_contradictory_lineage_or_model_refuses(monkeypatch, change):
    checked = recipe.checked

    def altered(path, sha):
        raw = checked(path, sha)
        if path == recipe.PINS["provenance"][0] and change == "consumer":
            value = json.loads(raw)
            value["runtime_consumer_sha256"][recipe.GUARD] = "0" * 64
        elif path == recipe.PINS["actual_review"][0] and change == "identity_review":
            value = json.loads(raw)
            value["actual_replacements"][0]["id"] = "f" * 64
        elif path == recipe.PINS["prior_models"][0] and change in {"command", "alias", "image"}:
            value = json.loads(raw)
            row = value["rows"][0]
            if change == "command":
                row["command"] = ["unreviewed"]
            elif change == "alias":
                next(iter(row["networks"].values()))["Aliases"] = ["unexpected"]
            else:
                row["image"] = "sha256:" + "f" * 64
        elif path == recipe.PINS["prior_runtime"][0] and change == "library":
            value = json.loads(raw)
            mapping = value["subjects"][5]["sources"]
            mapping[next(p for p in mapping if not p.startswith("/app/"))] = "0" * 64
        elif path == recipe.PINS["prior_provenance"][0] and change == "historical_basis":
            value = json.loads(raw)
            value["inherited_common_parent_memory_pins"] = 0
        else:
            return raw
        return recipe.install.canonical(value)

    monkeypatch.setattr(recipe, "checked", altered)
    with pytest.raises(ValueError):
        recipe.derive()
