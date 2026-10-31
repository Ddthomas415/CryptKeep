"""Offline v6 input derivation: no new native work, reservations or approvals."""
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess

import pytest

from scripts.research import companion_installer as install
from scripts.research import companion_staged_update as staged

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "docs/review_artifacts/companion_worker_preparation_20261023"
spec = importlib.util.spec_from_file_location("worker_inputs", HERE / "derive_inputs.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("input derivation attempted native/network work")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def synthetic_plan(candidate):
    approved = dict(candidate, decision="ACCEPTED_WITH_RISK", reviewer="SYNTHETIC TEST ONLY")
    raw = install.canonical(approved)
    return install.Plan.load(raw, hashlib.sha256(raw).hexdigest())


def test_only_twelve_allowed_fields_change_and_sources_preserved():
    previous = {key: (ROOT / path).read_bytes() for key, (path, _) in recipe.PINS.items()}
    candidate, provenance = recipe.derive()
    original = json.loads(previous["manifest"])
    restored = json.loads(json.dumps(candidate))
    for key in ("schema", "attempt", "decision", "reviewer"): restored[key] = original[key]
    for prior, app in zip(original["applications"], restored["applications"]):
        for key in ("command", "replacement_configured_metadata"): app[key] = prior[key]
    assert restored == original
    assert len(provenance["changed_manifest_fields"]) == 12
    assert len(provenance["source_entries"]) == 43 and provenance["source_changes"] == []
    assert all((ROOT / recipe.PINS[key][0]).read_bytes() == raw for key, raw in previous.items())


def test_draft_refused_and_synthetic_copy_exercises_exact_v6_shape():
    candidate, _ = recipe.derive()
    raw = install.canonical(candidate)
    with pytest.raises(install.core.Refused):
        install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    plan = synthetic_plan(candidate)
    assert plan.worker_shutdown and plan.staged and plan.running_storage
    assert set(plan.deferred_startup_policies) == install.STARTUP_POLICIES
    assert len(plan.applications) == 4


def test_predictions_are_not_new_container_or_image_evidence():
    candidate, provenance = recipe.derive()
    assert provenance["new_container_ids"] is None and provenance["new_image_ids"] is None
    assert all(p["evidence_label"] == "MODELLED" and p["new_container_id"] is None
               and p["new_image_id"] is None and p["historical_basis_removed"]
               and p["previous_prediction"] != p["predicted_final_metadata"] for p in provenance["predictions"])
    assert provenance["baseline_is_live_inventory"] is False
    assert len(provenance["preserve_old_stages_as_of_saved_inventory"]) == 4
    assert not any(provenance[k] for k in ("native_operations", "preparation_authorized", "startup_authorized", "cutover_authorized"))


def test_old_preparation_cannot_be_adopted_for_v6_attempt():
    candidate, _ = recipe.derive()
    evidence = json.loads((ROOT / recipe.OLD / "s3_source_refresh_plan/actual_preparation_evidence.json").read_bytes())
    with pytest.raises(install.core.Refused):
        staged._rows(synthetic_plan(candidate), evidence)


def test_changed_pinned_input_refuses(monkeypatch):
    path, _ = recipe.PINS["manifest"]
    monkeypatch.setitem(recipe.PINS, "manifest", (path, "0" * 64))
    with pytest.raises(ValueError, match="input_changed"):
        recipe.derive()


def test_changed_consumer_refuses(monkeypatch):
    monkeypatch.setitem(recipe.PREPARATION_CONSUMERS, "scripts/research/companion_prepare.py", "0" * 64)
    with pytest.raises(ValueError, match="input_changed"):
        recipe.derive()


@pytest.mark.parametrize("part", ["companion_preparations", "companion_cutovers"])
def test_consumed_marker_or_dangling_symlink_refuses_without_reserving(monkeypatch, part):
    original = recipe.os.path.lexists
    def occupied(path):
        return True if part in Path(path).parts else original(path)
    monkeypatch.setattr(recipe.os.path, "lexists", occupied)
    with pytest.raises(ValueError, match="attempt_already_used"):
        recipe.derive()


def test_derivation_reproduces_published_draft_and_provenance():
    candidate, provenance = recipe.derive()
    assert (HERE / "inputs/candidate_manifest.json").read_bytes() == install.canonical(candidate)
    assert (HERE / "inputs/provenance.json").read_bytes() == install.canonical(provenance)
