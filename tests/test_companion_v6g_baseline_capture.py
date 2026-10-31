"""Synthetic sanitized metadata; tests do not inspect the daemon."""
import importlib
import json

import pytest

from tests.test_companion_archive_contract import ROOT, offline


module = importlib.import_module(
    "docs.review_artifacts.companion_integration_inputs_v6g_20261025.capture_baseline")


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    offline(monkeypatch)
    monkeypatch.setattr(module, "CLI", ROOT / "scripts/research/collect_companion_recreation_metadata.py")
    import hashlib
    old = module.sources.checked
    manifest_path = module.sources.PINS["manifest"][0]

    def checked(path, sha):
        raw = old(path, sha)
        if path == manifest_path:
            value = json.loads(raw)
            value["cli_sha256"] = hashlib.sha256(module.CLI.read_bytes()).hexdigest()
            return json.dumps(value).encode()
        return raw

    monkeypatch.setattr(module.sources, "checked", checked)


def payload():
    return (ROOT / "docs/review_artifacts/companion_integration_inputs_v6f_20261025/capture_1.jsonl").read_bytes()


def test_exact_two_reads_and_raw_saved_before_validation(tmp_path):
    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        assert args[5:8] == ("container", "inspect", "--format")
        assert len(args[9:]) == 7
        assert kwargs["timeout"] <= 10 and kwargs["input_bytes"] is None
        if len(calls) == 2:
            assert (tmp_path / "out/capture_1.jsonl").read_bytes() == payload()
        return payload()

    report = module.capture(tmp_path / "out", runner)
    assert len(calls) == report["native_inspections"] == 2
    assert report["state"] == "READY_FOR_INDEPENDENT_REVIEW"
    assert report["observations"][0] == report["observations"][1]
    assert all("attempt" not in row for row in report["observations"][0])


@pytest.mark.parametrize("mode", ["malformed", "transport", "different"])
def test_failure_preserved_without_repeat(tmp_path, mode):
    calls = []

    def runner(*args, **kwargs):
        calls.append(1)
        if mode == "transport":
            raise TimeoutError("synthetic")
        if mode == "malformed":
            return b"not-json\n"
        return payload() if len(calls) == 1 else b"{}\n"

    report = module.capture(tmp_path / "out", runner)
    assert report["state"] == "INCOMPLETE"
    assert len(calls) == (2 if mode == "different" else 1)
    assert (tmp_path / "out/baseline_observation.json").is_file()
    if mode == "malformed":
        assert (tmp_path / "out/capture_1.jsonl").read_bytes() == b"not-json\n"


def test_existing_capture_directory_refused(tmp_path):
    output = tmp_path / "out"
    output.mkdir()
    with pytest.raises(FileExistsError):
        module.capture(output, lambda *_a, **_k: pytest.fail("must not inspect"))
