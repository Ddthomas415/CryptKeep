"""Offline source bindings and synthetic two-read capture; no daemon access."""
import ast
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import runpy
import sys

import pytest

from scripts.research import companion_installer as install
from tests.test_companion_archive_contract import ROOT, offline


PACKAGE = "docs.review_artifacts.companion_integration_inputs_v6i_20261027"
recipe = importlib.import_module(PACKAGE + ".refresh_sources")
capture = importlib.import_module(PACKAGE + ".capture_baseline")
HERE = ROOT / PACKAGE.replace(".", "/")


@pytest.fixture(autouse=True)
def no_operations(monkeypatch):
    offline(monkeypatch)


def test_only_accepted_application_and_host_hashes_change():
    result = recipe.refresh()
    assert json.loads((HERE / "source_refresh.json").read_bytes()) == result
    assert {d["path"] for d in result["source_deltas"]} == recipe.CHANGED
    assert len(result["consumer_sha256"]) == 13 and len(result["runtime_consumer_sha256"]) == 20
    assert sum(len(a["sources"]) for a in result["applications"]) == 43
    manifest = json.loads(recipe.checked(*recipe.PINS["manifest"]))
    prior = json.loads(recipe.checked(*recipe.PINS["sources"]))
    review = json.loads(recipe.checked(*recipe.PINS["repair_review"]))
    expected = deepcopy(manifest["applications"])
    changed = 0
    for app in expected:
        for source in app["sources"]:
            if source["local"] == recipe.MEMORY:
                assert app["name"] == "phase1-memory"
                source["sha256"] = review["hashes"][recipe.MEMORY]
                changed += 1
    assert changed == 1 and result["applications"] == expected
    assert result["consumer_sha256"] == prior["consumer_sha256"]
    assert set(result["runtime_consumer_sha256"]) == set(prior["runtime_consumer_sha256"])
    assert {p for p, h in prior["runtime_consumer_sha256"].items()
            if h != result["runtime_consumer_sha256"][p]} == {recipe.VERIFIER}
    assert result["source_deltas"][0]["lanes"] == ["application"]
    assert result["source_deltas"][1]["lanes"] == ["runtime"]
    assert result["changed_memory_image_policy"].startswith("UNVERIFIED")
    assert result["baseline"] is None and len(result["expected_original_targets"]) == 7
    assert result["new_container_ids"] is None and result["new_image_ids"] is None
    assert result["decision"] == "INCOMPLETE" and result["reviewer"] == ""
    assert not any(result[k] for k in ("preparation_authorized", "startup_authorized", "cutover_authorized", "query_authorized"))
    raw = install.canonical(result)
    with pytest.raises(install.core.Refused):
        install.Plan.load(raw, hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize("key", sorted(recipe.PINS))
def test_fixed_evidence_drift_refuses(monkeypatch, key):
    path, _ = recipe.PINS[key]
    monkeypatch.setitem(recipe.PINS, key, (path, "0" * 64))
    with pytest.raises(ValueError, match="source_refresh_drift"):
        recipe.refresh()


@pytest.mark.parametrize("path", [*sorted(recipe.CHANGED),
    "phase1_research_copilot/orchestrator/main.py", "scripts/research/companion_prepare.py"])
def test_current_consumer_or_application_drift_refuses(monkeypatch, path):
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"changed" if p == ROOT / path else read(p))
    with pytest.raises(ValueError, match="source_refresh_drift"):
        recipe.refresh()


@pytest.mark.parametrize("change", ["decision", "blocker", "operation_authority"])
def test_repair_review_cannot_be_promoted_from_invalid_state(monkeypatch, change):
    checked = recipe.checked

    def altered(path, sha):
        raw = checked(path, sha)
        if path == recipe.PINS["repair_review"][0]:
            value = json.loads(raw)
            if change == "decision": value["decision"] = "REJECTED"
            elif change == "blocker": value["blocking_findings"] = ["unresolved"]
            else: value["operations_authorized"] = True
            return json.dumps(value).encode()
        return raw

    monkeypatch.setattr(recipe, "checked", altered)
    with pytest.raises(ValueError, match="repair_not_reviewed"):
        recipe.refresh()


@pytest.mark.parametrize("lane", ["companion_preparations", "companion_cutovers"])
def test_proposed_label_never_reuses_consumption(monkeypatch, lane):
    exists = recipe.os.path.lexists
    monkeypatch.setattr(recipe.os.path, "lexists", lambda p: True
        if str(p).endswith(lane + "/" + recipe.PROPOSED) else exists(p))
    with pytest.raises(ValueError, match="proposed_label_consumed"):
        recipe.refresh()


@pytest.fixture
def synthetic_cli(monkeypatch):
    monkeypatch.setattr(capture, "CLI", ROOT / "scripts/research/collect_companion_recreation_metadata.py")
    checked = recipe.checked
    path = recipe.PINS["manifest"][0]

    def current(path_, sha):
        raw = checked(path_, sha)
        if path_ == path:
            value = json.loads(raw)
            value["cli_sha256"] = hashlib.sha256(capture.CLI.read_bytes()).hexdigest()
            return json.dumps(value).encode()
        return raw

    monkeypatch.setattr(recipe, "checked", current)


def payload():
    return (ROOT / "docs/review_artifacts/companion_integration_inputs_v6f_20261025/capture_1.jsonl").read_bytes()


def test_two_bounded_reads_preserve_first_bytes_before_second(tmp_path, synthetic_cli):
    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        assert args[5:8] == ("container", "inspect", "--format") and len(args[9:]) == 7
        assert kwargs["timeout"] <= 10 and kwargs["input_bytes"] is None
        assert kwargs["limit"] == 1_048_576 and kwargs["env"] == {"PATH": "/usr/bin:/bin"}
        if len(calls) == 2:
            assert (tmp_path / "out/capture_1.jsonl").read_bytes() == payload()
        return payload()

    result = capture.capture(tmp_path / "out", runner)
    assert len(calls) == result["native_inspections"] == 2
    assert result["state"] == "READY_FOR_INDEPENDENT_REVIEW"
    assert result["selected_observations_equal"] and result["metadata_complete_for_selected_fields"]


@pytest.mark.parametrize("mode", ["malformed", "transport", "different", "missing_flags"])
def test_failed_capture_preserves_evidence_and_never_repeats(tmp_path, synthetic_cli, mode):
    calls = []

    def runner(*args, **kwargs):
        calls.append(True)
        if mode == "transport": raise TimeoutError("synthetic")
        if mode == "malformed": return b"not-json\n"
        if mode == "missing_flags": return b"{}\n" * 7
        return payload() if len(calls) == 1 else b"{}\n"

    result = capture.capture(tmp_path / "out", runner)
    assert result["state"] == "INCOMPLETE"
    assert len(calls) == (1 if mode in {"malformed", "transport"} else 2)
    assert (tmp_path / "out/baseline_observation.json").is_file()
    if mode == "malformed": assert (tmp_path / "out/capture_1.jsonl").read_bytes() == b"not-json\n"


def test_existing_capture_directory_is_not_overwritten(tmp_path, synthetic_cli):
    output = tmp_path / "out"
    output.mkdir()
    with pytest.raises(FileExistsError):
        capture.capture(output, lambda *_a, **_k: pytest.fail("must not inspect"))


def test_capture_body_only_changes_temporary_prefix_vs_reviewed_v6h():
    old = (ROOT / "docs/review_artifacts/companion_integration_inputs_v6h_20261026/capture_baseline.py").read_text()
    new = (HERE / "capture_baseline.py").read_text()
    def body(text):
        return ast.dump(next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == "capture"))
    assert body(old.replace("ck-v6h-metadata-", "ck-v6i-metadata-")) == body(new)


def test_default_entrypoint_does_not_read_cli_or_capture(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["capture_baseline.py"])
    monkeypatch.delitem(sys.modules, PACKAGE + ".capture_baseline")
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: pytest.fail("must not read Docker CLI")
        if str(p).startswith("/Applications/") else read(p))
    runpy.run_module(PACKAGE + ".capture_baseline", run_name="__main__")
    assert json.loads(capsys.readouterr().out) == {"actions_executed": False, "state": "INCOMPLETE"}
