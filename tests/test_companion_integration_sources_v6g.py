"""Offline inputs only; no synthetic baseline is published as an observation."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

from scripts.research import companion_installer as install
from tests.test_companion_archive_contract import ROOT, offline


PATH = ROOT / "docs/review_artifacts/companion_integration_inputs_v6g_20261025/refresh_sources.py"
spec = importlib.util.spec_from_file_location("integration_sources_v6g", PATH)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


@pytest.fixture(autouse=True)
def no_operations(monkeypatch):
    offline(monkeypatch)


def test_source_only_delta_never_claims_current_baseline_or_permission():
    result = recipe.refresh()
    assert result["baseline"] is None and result["reviewer"] == ""
    assert result["new_container_ids"] is None and result["new_image_ids"] is None
    assert result["decision"] == "INCOMPLETE"
    assert not any(result[k] for k in ("preparation_authorized", "startup_authorized", "cutover_authorized", "query_authorized"))
    assert len(result["runtime_consumer_sha256"]) == 20
    assert len(result["consumer_sha256"]) == 13
    assert len(result["expected_original_targets"]) == 7
    assert result["source_deltas"] == [{
        "path": recipe.GUARD, "before": "d003edac94edbb7d7886901784674e23ed9accae2d42bd69c0a7f6fbc0c9e381",
        "after": "18bc1966511bc9d1e0a2b722b973be357672e2bb6b951721628eb98262f4dfec",
        "lane": "host_runtime_consumer_only"}]
    raw = install.canonical(result)
    with pytest.raises(install.core.Refused):
        install.Plan.load(raw, hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize("key", sorted(recipe.PINS))
def test_fixed_input_drift_refuses(monkeypatch, key):
    path, _ = recipe.PINS[key]
    monkeypatch.setitem(recipe.PINS, key, (path, "0" * 64))
    with pytest.raises(ValueError, match="source_refresh_drift"):
        recipe.refresh()


@pytest.mark.parametrize("path", [recipe.GUARD, "phase1_research_copilot/orchestrator/main.py",
                                 "scripts/research/companion_prepare.py"])
def test_current_source_or_tool_drift_refuses(monkeypatch, path):
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"changed" if p == ROOT / path else read(p))
    with pytest.raises(ValueError, match="source_refresh_drift"):
        recipe.refresh()


def test_consumed_new_label_refuses_without_reset(monkeypatch):
    exists = recipe.os.path.lexists
    monkeypatch.setattr(recipe.os.path, "lexists", lambda p: True if str(p).endswith(recipe.PROPOSED) else exists(p))
    with pytest.raises(ValueError, match="proposed_label_consumed"):
        recipe.refresh()


def test_application_commands_and_source_paths_are_unchanged():
    result = recipe.refresh()
    import json
    prior = json.loads(recipe.checked(*recipe.PINS["manifest"]))
    assert result["applications"] == prior["applications"]
    assert sum(len(a["sources"]) for a in result["applications"]) == 43
