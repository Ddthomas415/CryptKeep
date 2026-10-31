"""Offline V6f composition; external approvals in temporary fixtures only."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
from types import SimpleNamespace

import pytest

from scripts.research import companion_cutover as entry, companion_runtime_adapter as adapter
from tests.test_companion_archive_contract import ROOT, offline
from tests.test_companion_runtime_adapter import seal_fixture_reviews

BASE = ROOT / "docs/review_artifacts/companion_integration_inputs_v6f_20261025"
spec = importlib.util.spec_from_file_location("v6f_packet", BASE / "assemble_runtime_packet.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def no_operations(monkeypatch):
    offline(monkeypatch)
    def forbidden(*a, **kw):
        raise AssertionError("packet attempted lifecycle/token/reservation")
    monkeypatch.setattr(entry, "DockerInstallBackend", forbidden)
    monkeypatch.setattr(entry, "_reserve", forbidden)
    monkeypatch.setattr(adapter, "token_from_pipe", forbidden)


def test_exact_actual_ids_changed_memory_only_and_truthful_provenance():
    artifacts = recipe.derive()
    prior = json.loads(recipe.checked(*recipe.PINS["prior_runtime"]))
    subjects, proof = artifacts["subjects.draft.json"], artifacts["provenance.json"]
    assert subjects[:3] == prior["subjects"][:3] and len(artifacts) == 12
    for before, now in zip(prior["subjects"][3:], subjects[3:]):
        assert before["container_id"] != now["container_id"]
        changed = {p for p in now["sources"] if now["sources"][p] != before["sources"][p]}
        assert set(now["sources"]) == set(before["sources"])
        assert changed == (recipe.MEMORY_CHANGES if now["name"] == "phase1-memory" else set())
        assert (now["image_id"] != before["image_id"]) == (now["name"] == "phase1-memory")
    assert proof["total_source_pins"] == 132
    assert proof["application_entries_controller_attested"] == 43 and proof["direct_file_streams_recaptured"] == 0
    assert proof["inherited_exact_image_or_storage_pins"] == 52
    assert proof["inherited_common_parent_memory_pins"] == 37
    assert len(proof["consumer_sha256"]) == 20
    assert [r["document_id"] for r in artifacts["topical_approvals.json"]] == [7,5,47,18]
    for name, value in artifacts.items():
        if name.endswith(".draft.json") and name != "subjects.draft.json":
            assert value["decision"] == "INCOMPLETE" and value["reviewer"] == ""
            assert set(value.get("policies",{}).values()) <= {"UNVERIFIED"}


def test_actual_loader_composition_under_synthetic_temporary_reviews_only(tmp_path):
    artifacts = recipe.derive()
    subjects = artifacts["subjects.draft.json"]
    pins = adapter.ReviewedPins(tuple(adapter.TargetPin(s["name"],s["container_id"],s["image_id"],
        s["preservation_sha256"],tuple(sorted(s["sources"].items()))) for s in subjects),
        "0"*64,(),tuple(artifacts["topical_approvals.json"]),b"",())
    pins = seal_fixture_reviews(pins)
    runtime = json.loads(pins.review_manifest)
    runtime.update(schema="companion-runtime-pins-v2",network_configuration=artifacts["runtime_review.draft.json"]["network_configuration"])
    raw = adapter._canonical(runtime)
    pins = replace(pins,review_manifest=raw,review_record_sha256=hashlib.sha256(raw).hexdigest())
    for name in ("staged_metadata.derived.json","topical_approvals.json"):
        (tmp_path/name).write_bytes(adapter._canonical(artifacts[name]))
    (tmp_path/"runtime.json").write_bytes(raw)
    children=[]
    for index,value in enumerate(pins.dependency_review_records):
        p=tmp_path/f"synthetic-{index}.json";p.write_bytes(value);children.append(p)
    args=SimpleNamespace(manifest=ROOT/recipe.PINS["manifest"][0],reviewed_manifest_sha256=recipe.PINS["manifest"][1],
        preparation_evidence=ROOT/recipe.PINS["evidence"][0],preparation_review=ROOT/recipe.PINS["id_review"][0],
        reviewed_preparation_review_sha256=recipe.PINS["id_review"][1],staged_metadata=tmp_path/"staged_metadata.derived.json",
        runtime_review=tmp_path/"runtime.json",reviewed_runtime_review_sha256=pins.review_record_sha256,
        topical_approvals=tmp_path/"topical_approvals.json",dependency_review=children)
    plan,prepared,loaded=entry.load_inputs(args)
    assert loaded==pins and len(prepared.replacements)==4 and plan.attempt=="workerprep20261025v6f"


@pytest.mark.parametrize("key", ["manifest","id_review","actual_review","postcheck","repair_review","prior_scope","builder","staged_flow","topical"])
def test_hash_drift_refuses(monkeypatch,key):
    path,_=recipe.PINS[key];monkeypatch.setitem(recipe.PINS,key,(path,"0"*64))
    with pytest.raises(ValueError,match="input_changed"):
        recipe.derive()


@pytest.mark.parametrize("change", ["original","stage","alias","command","pair","identity_review","consumer","parent","prior_library","old_source"])
def test_contradictory_saved_evidence_or_lineage_refuses(monkeypatch,change):
    original=recipe.checked
    def altered(path,sha):
        raw=original(path,sha)
        if path==recipe.PINS["postcheck"][0] and change in {"original","stage","alias","command","pair"}:
            value=json.loads(raw)
            if change=="pair":value["after"][7]["started"]="changed"
            else:
                row=value["before"][0 if change=="original" else 7]
                if change in {"original","stage"}:row["id"]="f"*64
                elif change=="alias":next(iter(row["networks"].values()))["Aliases"]=["unexpected"]
                else:row["command"]=["unreviewed"]
                value["after"]=deepcopy(value["before"])
            return adapter._canonical(value)
        if path==recipe.PINS["actual_review"][0] and change=="identity_review":
            value=json.loads(raw);value["accepted_actual_stages"][2]["image"]="sha256:"+"f"*64
            return adapter._canonical(value)
        if path==recipe.PINS["provenance"][0] and change=="consumer":
            value=json.loads(raw);value["consumer_sha256"][recipe.INSTALLER]="0"*64
            return adapter._canonical(value)
        if path==recipe.PINS["prior_manifest"][0] and change=="parent":
            value=json.loads(raw);value["baseline"][5]["image"]="sha256:"+"f"*64
            return adapter._canonical(value)
        if path==recipe.PINS["prior_runtime"][0] and change=="prior_library":
            value=json.loads(raw);sources=value["subjects"][5]["sources"]
            sources[next(p for p in sources if not p.startswith("/app/"))]="0"*64
            return adapter._canonical(value)
        if path==recipe.PINS["repair"][0] and change=="old_source":
            value=json.loads(raw);value["pre_change_source_sha256"]["phase1_research_copilot/memory_retrieval/article_view.py"]="0"*64
            return adapter._canonical(value)
        return raw
    monkeypatch.setattr(recipe,"checked",altered)
    with pytest.raises(ValueError):
        recipe.derive()
