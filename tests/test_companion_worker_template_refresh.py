"""Offline proposal checks; never reserve an attempt or invoke native work."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

from scripts.research import companion_installer as install
from scripts.research import companion_staged_update as staged

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "docs/review_artifacts/companion_worker_preparation_20261023"
spec = importlib.util.spec_from_file_location("template_refresh", HERE / "derive_template_refresh.py")
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw): raise AssertionError("template refresh attempted native work")
    monkeypatch.setattr(subprocess, "Popen", forbidden)


def test_only_attempt_and_review_fields_change_with_one_consumer_binding():
    candidate, provenance = recipe.derive()
    old = json.loads((HERE / "inputs/reviewed_preparation_manifest.json").read_bytes())
    restored = dict(candidate, attempt=old["attempt"], decision=old["decision"], reviewer=old["reviewer"])
    assert restored == old
    assert len(provenance["consumer_changes"]) == 1
    assert provenance["application_source_changes"] == provenance["predicted_metadata_changes"] == []
    assert provenance["new_container_ids"] is None and not provenance["preparation_authorized"]


def test_draft_is_refused_and_old_evidence_cannot_cross_attempt():
    candidate, _ = recipe.derive()
    raw = install.canonical(candidate)
    with pytest.raises(install.core.Refused): install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    candidate.update(decision="ACCEPTED_WITH_RISK", reviewer="SYNTHETIC TEST ONLY")
    raw = install.canonical(candidate)
    plan = install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    old = {"schema":"companion-staged-preparation-v1","state":"READY_FOR_INDEPENDENT_REVIEW",
           "manifest_sha256":plan.manifest_sha256,"attempt":"workerprep20261023v6a","replacements":[]}
    with pytest.raises(install.core.Refused): staged._rows(plan, old)


def test_changed_repair_hash_refuses(monkeypatch):
    monkeypatch.setattr(recipe, "NEW_BACKEND", "0" * 64)
    with pytest.raises(ValueError, match="single_expression"): recipe.derive()


def test_occupied_attempt_refuses(monkeypatch):
    monkeypatch.setattr(recipe.os.path, "lexists", lambda path: True)
    with pytest.raises(ValueError, match="attempt_occupied"): recipe.derive()


def test_reproduces_both_published_draft_files():
    candidate, provenance = recipe.derive()
    assert (HERE / "refresh_inputs/candidate_manifest.json").read_bytes() == install.canonical(candidate)
    assert (HERE / "refresh_inputs/provenance.json").read_bytes() == install.canonical(provenance)
