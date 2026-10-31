"""Offline V6c handoff; all source responses/tokens are synthetic."""
import json
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace

import pytest

from docs.review_artifacts.companion_worker_preparation_20261023 import execute_reviewed_v6c as handoff
from scripts.research import companion_cutover as cutover
from scripts.research import companion_docker_transport as transport
from scripts.research.companion_runtime_adapter import token_from_pipe

TOKEN = "synthetic-v6c-token"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("native/network operation forbidden")
    monkeypatch.setattr(transport, "_run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    common = handoff.helpers()
    source = SimpleNamespace(name="phase1-orchestrator", id="a" * 64, image="sha256:" + "b" * 64)
    plan = SimpleNamespace(baseline=[source], attempt="syntheticv6c01")
    argv, calls = ["--synthetic-input", "fixture"], []
    monkeypatch.setattr(handoff, "ROOT", tmp_path)
    monkeypatch.setattr(handoff, "validated", lambda: (common, argv, plan))
    monkeypatch.setattr(handoff.resource, "setrlimit", lambda *a: None)
    monkeypatch.setattr(handoff.os, "chdir", lambda *a: None)
    monkeypatch.setattr(transport.DockerTransport, "_verify_cli", lambda *a: True)
    def native(args, **kwargs):
        calls.append(("source", args, kwargs))
        assert args[-1] == source.id and common.source_format(source) in args
        assert kwargs == dict(timeout=10, input_bytes=None, limit=8192, env=dict(transport.ENV))
        return json.dumps("SERVICE_TOKEN=" + TOKEN).encode()
    monkeypatch.setattr(transport, "_run", native)
    def invoke(actual):
        calls.append(("consumer", actual))
        fd = int(actual[actual.index("--token-fd") + 1])
        assert token_from_pipe(fd) == TOKEN
        return 23
    monkeypatch.setattr(cutover, "main", invoke)
    return SimpleNamespace(calls=calls, root=tmp_path, plan=plan)


def test_helper_identity_and_no_old_launcher_invocation(monkeypatch):
    common = handoff.helpers()
    assert common.__name__ != "__main__"
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"raise AssertionError('must not execute')" if p == handoff.OLD_HELPER else read(p))
    with pytest.raises(ValueError, match="reviewed_helper_changed"):
        handoff.helpers()


def test_actual_accepted_v2_inputs_load_without_native_or_credentials():
    _, argv, plan = handoff.validated()
    assert plan.attempt == "workerprep20261023v6c" and len(plan.network_bindings) == 1
    assert "--execute-cutover" not in argv and "--token-fd" not in argv


def test_default_is_inert(monkeypatch, capsys):
    def forbidden(*a, **kw):
        raise AssertionError("default invoked operations")
    for name in ("DockerTransport", "DockerInstallBackend", "_reserve"):
        monkeypatch.setattr(cutover, name, forbidden)
    monkeypatch.setattr(cutover.adapter, "token_from_pipe", forbidden)
    monkeypatch.setattr(cutover.fcntl, "flock", forbidden)
    assert handoff.validate_only() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["input_bindings_validated"] and not result["actions_executed"]


@pytest.mark.parametrize("field", ["RECEIPT_SHA", "REVIEW_SHA", "SCOPE_SHA", "RUNTIME_SHA"])
def test_record_hash_drift_refuses_before_token(monkeypatch, field):
    monkeypatch.setattr(handoff, field, "0" * 64)
    with pytest.raises(ValueError, match="reviewed_input_changed"):
        handoff.validated()


def test_current_consumer_drift_refuses(monkeypatch):
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"changed" if p.name == "companion_cutover.py" else read(p))
    with pytest.raises(ValueError, match="reviewed_consumer_changed"):
        handoff.validated()


@pytest.mark.parametrize("change", ["execution_flag", "receipt_failure", "scope_detached", "network", "subjects"])
def test_cross_record_contradictions_refuse(monkeypatch, change):
    common = handoff.helpers()
    original = common.checked_json
    def altered(path, sha):
        value = original(path, sha)
        if path.name == "inert_validation_receipt.json":
            if change == "execution_flag":
                value["argv"].append("--execute-cutover")
            elif change == "receipt_failure":
                value["stdout"]["actions_executed"] = True
        if path.name == "runtime_review.json":
            if change == "scope_detached":
                value["reviewer"] = "unbound"
            elif change == "network":
                value["network_configuration"]["bindings"] = {}
            elif change == "subjects":
                value["subjects"][3]["container_id"] = "f" * 64
        return value
    monkeypatch.setattr(common, "checked_json", altered)
    monkeypatch.setattr(handoff, "helpers", lambda: common)
    with pytest.raises(ValueError):
        handoff.validated()


def test_one_private_source_read_then_one_pipe_handoff(synthetic, capsys):
    assert handoff.execute() == 23
    assert [c[0] for c in synthetic.calls] == ["source", "consumer"]
    assert TOKEN not in repr(synthetic.calls) and capsys.readouterr().out == ""


@pytest.mark.parametrize("kind", ["directory", "broken_symlink"])
def test_consumed_cutover_refuses_before_token(synthetic, capsys, kind):
    destination = synthetic.root.joinpath(*cutover.STATE_PARTS, synthetic.plan.attempt)
    destination.parent.mkdir(parents=True)
    if kind == "directory":
        destination.mkdir()
    else:
        destination.symlink_to(synthetic.root / "absent")
    assert handoff.execute() == 1 and synthetic.calls == []
    assert not json.loads(capsys.readouterr().out)["entrypoint_handoff_entered"]


def test_cli_refusal_reads_no_token(synthetic, monkeypatch, capsys):
    monkeypatch.setattr(transport.DockerTransport, "_verify_cli", lambda *a: False)
    assert handoff.execute() == 1 and synthetic.calls == []
    assert TOKEN not in capsys.readouterr().out


@pytest.mark.parametrize("raw", [b"", b"bad-json", b'"SERVICE_TOKEN="',
    b'"SERVICE_TOKEN=synthetic"\n"SERVICE_TOKEN=duplicate"', b'"SERVICE_TOKEN=has space"'])
def test_bad_token_source_refuses_without_handoff(synthetic, monkeypatch, capsys, raw):
    reads = []
    monkeypatch.setattr(transport, "_run", lambda *a, **kw: reads.append(True) or raw)
    assert handoff.execute() == 1 and reads == [True] and synthetic.calls == []
    assert TOKEN not in capsys.readouterr().out


def test_native_exception_is_sanitized_without_retry(synthetic, monkeypatch, capsys):
    reads = []
    def fail(*a, **kw):
        reads.append(True)
        raise RuntimeError(TOKEN)
    monkeypatch.setattr(transport, "_run", fail)
    assert handoff.execute() == 1 and reads == [True]
    captured = capsys.readouterr()
    assert TOKEN not in captured.out and captured.err == ""
