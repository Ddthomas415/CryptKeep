"""Sanitized collection failures never execute lifecycle or unverified binaries."""
import json
from pathlib import Path

import pytest

from scripts.research import collect_companion_recreation_metadata as capture


def test_unverified_cli_refuses_before_runner_or_output(tmp_path, monkeypatch):
    cli = tmp_path / "cli"
    cli.write_bytes(b"wrong binary")
    monkeypatch.setattr(capture, "CLI", cli)
    calls = []
    with pytest.raises(ValueError, match="cli_identity_changed"):
        capture.collect(tmp_path, tmp_path / "out", lambda *a, **kw: calls.append(a))
    assert calls == [] and not (tmp_path / "out").exists()


def test_capture_format_omits_raw_environment_and_unknown_command_dump():
    template = capture.capture_format()
    assert "{{json .Config.Env}}" not in template
    assert "{{json .Config.Labels}}" not in template
    assert '"command_recognized"' in template
    assert '"healthcheck_recognized"' in template
    assert '"PYTHONPATH_matches"' in template
    assert "{{if and " == template[:9]
    assert '(index .HostConfig "Init")' in template
    assert ".HostConfig.Init" not in template


def test_native_error_detail_does_not_export_stderr_values(monkeypatch):
    from types import SimpleNamespace
    def failed(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout=b"", stderr=(
            b'template: :1: at <.HostConfig.Init>: unknown field; synthetic-secret=never-export'))
    monkeypatch.setattr(capture.subprocess, "run", failed)
    with pytest.raises(capture.CaptureFailure) as error:
        capture.readonly_run(("synthetic",), timeout=1, input_bytes=None, limit=100, env={})
    assert error.value.category == "metadata_template_error:.hostconfig.init"
    assert "secret" not in str(error.value)


def test_reconcile_uses_only_full_metadata_not_unknown_fallback():
    assert capture.reconcile([{"id": "a" * 64, "command_recognized": False}]) == []


def test_manifest_reconciliation_refuses_unverified_or_mismatched_evidence():
    with pytest.raises(ValueError, match="reconciliation_evidence_incomplete"):
        capture.reconcile_manifest({"state": "INCOMPLETE"}, b"{}")
    with pytest.raises(ValueError, match="reconciliation_evidence_incomplete"):
        capture.reconcile_manifest({"state": "READY_FOR_INDEPENDENT_REVIEW", "final_observations_match": True,
                                  "metadata_complete_for_selected_fields": True, "source_manifest_sha256": "wrong"}, b"{}")


def test_transport_failure_persists_only_category_and_no_retry(tmp_path, monkeypatch):
    cli = tmp_path / "cli"
    cli.write_bytes(b"synthetic CLI")
    monkeypatch.setattr(capture, "CLI", cli)
    monkeypatch.setattr(capture, "CLI_SHA256", capture.hashlib.sha256(cli.read_bytes()).hexdigest())
    evidence = tmp_path / "docs/review_artifacts"
    evidence.mkdir(parents=True)
    (evidence / "companion_compatibility_20261016.json").write_text(json.dumps({"targets": [{"id": "a" * 64}]}))
    source = evidence / "companion_install_manifest_20261017"
    source.mkdir()
    (source / "manifest.json").write_text("{}")
    calls = []
    def failed(argv, *, timeout, input_bytes, limit, env):
        calls.append(argv)
        assert argv[5:7] == ("container", "inspect")
        assert env == {"PATH": "/usr/bin:/bin"} and input_bytes is None
        raise RuntimeError("synthetic-sensitive-payload-must-not-be-saved")
    report = capture.collect(tmp_path, tmp_path / "out", failed)
    raw = (tmp_path / "out/observation.json").read_text()
    assert len(calls) == 1 and report["state"] == "INCOMPLETE"
    assert "synthetic-sensitive" not in raw and report["failure_category"] == "RuntimeError"


@pytest.mark.parametrize("use_current", [False, True])
def test_capture_binds_explicit_manifest_without_changing_default(tmp_path, monkeypatch, use_current):
    root = Path(__file__).resolve().parents[1]
    cli = tmp_path / "cli"
    cli.write_bytes(b"synthetic CLI")
    monkeypatch.setattr(capture, "CLI", cli)
    monkeypatch.setattr(capture, "CLI_SHA256", capture.hashlib.sha256(cli.read_bytes()).hexdigest())
    artifacts = tmp_path / "docs/review_artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "companion_compatibility_20261016.json").write_bytes(
        (root / "docs/review_artifacts/companion_compatibility_20261016.json").read_bytes())
    legacy = artifacts / "companion_install_manifest_20261017/manifest.json"
    current = artifacts / "current_sources/manifest.json"
    for path, raw in ((legacy, b'{"source":"legacy"}'), (current, b'{"source":"current"}')):
        path.parent.mkdir()
        path.write_bytes(raw)
    fixture = json.loads((root / "docs/review_artifacts/companion_batch_closeout_20261017/capture/observation.json").read_bytes())
    calls = []
    def inspect_only(argv, **kwargs):
        calls.append(argv)
        assert argv[5:7] == ("container", "inspect") and kwargs["input_bytes"] is None
        assert kwargs["env"] == {"PATH": "/usr/bin:/bin"}
        return b"\n".join(json.dumps(row).encode() for row in fixture["observations"])
    selected = current if use_current else legacy
    report = capture.collect(tmp_path, tmp_path / "out", inspect_only,
                             source_manifest=current.relative_to(tmp_path) if use_current else None)
    assert report["state"] == "READY_FOR_INDEPENDENT_REVIEW" and len(calls) == 2
    assert report["source_manifest_sha256"] == capture.hashlib.sha256(selected.read_bytes()).hexdigest()
    assert report["source_manifest_path"] == selected.relative_to(tmp_path).as_posix()
    assert report["installation_authorized"] is False


@pytest.mark.parametrize("kind", ["outside", "symlink", "oversized", "directory"])
def test_bad_manifest_refused_before_capture_or_output(tmp_path, monkeypatch, kind):
    cli = tmp_path / "cli"
    cli.write_bytes(b"synthetic CLI")
    monkeypatch.setattr(capture, "CLI", cli)
    monkeypatch.setattr(capture, "CLI_SHA256", capture.hashlib.sha256(cli.read_bytes()).hexdigest())
    artifacts = tmp_path / "docs/review_artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "companion_compatibility_20261016.json").write_text('{"targets":[]}')
    manifest = artifacts / "manifest.json"
    if kind == "outside":
        manifest = tmp_path / "manifest.json"
        manifest.write_text("{}")
    elif kind == "symlink":
        target = artifacts / "target.json"
        target.write_text("{}")
        manifest.symlink_to(target)
    elif kind == "oversized":
        manifest.write_bytes(b"x" * 1_048_577)
    else:
        manifest.mkdir()
    calls = []
    with pytest.raises(ValueError, match="source_manifest_"):
        capture.collect(tmp_path, tmp_path / "out", lambda *a, **k: calls.append(a), source_manifest=manifest)
    assert not calls and not (tmp_path / "out").exists()
