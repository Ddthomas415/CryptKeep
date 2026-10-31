import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from scripts.research import companion_installer as install
from scripts.research import companion_staged_update as staged

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs/review_artifacts/companion_continuation_20261021/derive_s3_refresh_plan.py"
spec = importlib.util.spec_from_file_location("source_refresh", SCRIPT)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


def test_exact_one_source_change_and_preserved_old_inputs():
    before = {name: (recipe.HERE / name).read_bytes() for name in recipe.PINS}
    candidate, evidence = recipe.derive()
    original = json.loads(before["preparation_reconciled_manifest.json"])
    restored = json.loads(json.dumps(candidate))
    restored.update(attempt=original["attempt"], decision=original["decision"], reviewer=original["reviewer"])
    restored["applications"][2]["sources"][2]["sha256"] = recipe.OLD_MAIN
    assert restored == original
    assert len(evidence["source_entries"]) == 43 and len(evidence["source_changes"]) == 1
    assert all((recipe.HERE / name).read_bytes() == raw for name, raw in before.items())
    assert len(evidence["preserve_old_prepared_subjects"]) == 4
    assert evidence["native_operations"] is False and evidence["new_container_ids"] is None


def test_unaccepted_draft_is_not_an_executable_plan():
    candidate, _ = recipe.derive()
    raw = recipe.canonical(candidate)
    with pytest.raises(install.core.Refused):
        install.Plan.load(raw, hashlib.sha256(raw).hexdigest())


def test_shape_validates_only_with_explicit_synthetic_approval_copy():
    candidate, _ = recipe.derive()
    candidate.update(decision="ACCEPTED_WITH_RISK", reviewer="SYNTHETIC TEST ONLY - NOT AN APPROVAL")
    raw = recipe.canonical(candidate)
    plan = install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    assert plan.staged and len(plan.applications) == 4
    assert set(plan.deferred_startup_policies) == install.STARTUP_POLICIES


def test_old_preparation_is_not_adoptable_under_new_attempt():
    candidate, _ = recipe.derive()
    candidate.update(decision="ACCEPTED_WITH_RISK", reviewer="SYNTHETIC TEST ONLY")
    raw = recipe.canonical(candidate)
    plan = install.Plan.load(raw, hashlib.sha256(raw).hexdigest())
    old = json.loads((recipe.HERE / "preparation_reconciled_evidence.json").read_bytes())
    with pytest.raises(install.core.Refused):
        staged._rows(plan, old)


def test_changed_review_or_input_refuses(monkeypatch):
    monkeypatch.setitem(recipe.PINS, "companion_s3_single_attempt_review_20261021.json", "0" * 64)
    with pytest.raises(ValueError, match="refresh_input_changed"):
        recipe.derive()


def test_mismatched_repair_refuses(monkeypatch):
    monkeypatch.setattr(recipe, "NEW_MAIN", "0" * 64)
    with pytest.raises(ValueError):
        recipe.derive()


def test_uses_separate_unconsumed_attempt_and_retains_false_startup_policies():
    candidate, evidence = recipe.derive()
    assert candidate["attempt"] != evidence["previous_attempt"]
    assert candidate["policies"]["sdk_startup_compatible"] is False
    assert candidate["policies"]["source_imports_frozen"] is False
    assert evidence["baseline_is_live_inventory"] is False
    assert evidence["preparation_authorized"] is False
    assert evidence["startup_authorized"] is False and evidence["cutover_authorized"] is False
