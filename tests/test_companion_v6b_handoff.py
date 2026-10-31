"""Offline handoff checks; all native responses and tokens are synthetic."""
import json
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace

import pytest

from docs.review_artifacts.companion_worker_preparation_20261023 import execute_reviewed_v6b as handoff
from scripts.research import companion_cutover as cutover
from scripts.research import companion_docker_transport as transport
from scripts.research.companion_runtime_adapter import token_from_pipe

TOKEN = "synthetic-v6b-token"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
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
    plan = SimpleNamespace(baseline=[source], attempt="syntheticv6b01")
    argv = ["--synthetic-input", "fixture"]
    calls = []
    monkeypatch.setattr(handoff, "ROOT", tmp_path)
    monkeypatch.setattr(handoff, "validated", lambda: (common, argv, plan))
    monkeypatch.setattr(handoff.resource, "setrlimit", lambda *args: None)
    monkeypatch.setattr(handoff.os, "chdir", lambda *args: None)
    monkeypatch.setattr(transport.DockerTransport, "_verify_cli", lambda *args: True)
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


def test_helper_hash_guard_does_not_invoke_old_launcher(monkeypatch):
    common = handoff.helpers()
    assert common.__name__ != "__main__"
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"raise AssertionError('must not execute')" if p == handoff.OLD_HELPER else read(p))
    with pytest.raises(ValueError, match="reviewed_helper_changed"):
        handoff.helpers()


def test_actual_accepted_inputs_are_loaded_without_native_or_credentials():
    _, argv, plan = handoff.validated()
    assert plan.attempt == handoff.ATTEMPT
    assert "--execute-cutover" not in argv and "--token-fd" not in argv


def test_default_entrypoint_is_inert_and_never_constructs_native_backend(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("inert path tried a native/credential/reservation operation")
    monkeypatch.setattr(cutover, "DockerTransport", forbidden)
    monkeypatch.setattr(cutover, "DockerInstallBackend", forbidden)
    monkeypatch.setattr(cutover, "_reserve", forbidden)
    monkeypatch.setattr(cutover.adapter, "token_from_pipe", forbidden)
    assert handoff.validate_only() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["input_bindings_validated"] and not result["actions_executed"]


@pytest.mark.parametrize("field", ["RECEIPT_SHA", "REVIEW_SHA", "SCOPE_SHA", "RUNTIME_SHA"])
def test_record_hash_drift_refuses_before_source_read(monkeypatch, field):
    monkeypatch.setattr(handoff, field, "0" * 64)
    with pytest.raises(ValueError, match="reviewed_input_changed"):
        handoff.validated()


def test_consumer_drift_refuses_before_import_or_source(monkeypatch):
    read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"changed" if p.name == "companion_cutover.py" else read(p))
    with pytest.raises(ValueError, match="reviewed_consumer_changed"):
        handoff.validated()


def test_source_then_consumer_called_once_with_private_pipe(synthetic, capsys):
    assert handoff.execute() == 23
    assert [x[0] for x in synthetic.calls] == ["source", "consumer"]
    assert TOKEN not in repr(synthetic.calls) and capsys.readouterr().out == ""


@pytest.mark.parametrize("kind", ["directory", "broken_symlink"])
def test_consumed_destination_refuses_before_any_source(synthetic, capsys, kind):
    destination = synthetic.root.joinpath(*cutover.STATE_PARTS, synthetic.plan.attempt)
    destination.parent.mkdir(parents=True)
    if kind == "directory":
        destination.mkdir()
    else:
        destination.symlink_to(synthetic.root / "absent")
    assert handoff.execute() == 1 and synthetic.calls == []
    assert not json.loads(capsys.readouterr().out)["entrypoint_handoff_entered"]


def test_cli_hash_failure_reads_no_token(synthetic, monkeypatch, capsys):
    monkeypatch.setattr(transport.DockerTransport, "_verify_cli", lambda *args: False)
    assert handoff.execute() == 1 and synthetic.calls == []
    assert TOKEN not in capsys.readouterr().out


@pytest.mark.parametrize("raw", [b"", b"bad-json", b'"SERVICE_TOKEN="',
    b'"SERVICE_TOKEN=synthetic"\n"SERVICE_TOKEN=duplicate"', b'"SERVICE_TOKEN=has space"'])
def test_invalid_or_ambiguous_source_refuses_consumer(synthetic, monkeypatch, capsys, raw):
    sources = []
    monkeypatch.setattr(transport, "_run", lambda *args, **kwargs: sources.append(True) or raw)
    assert handoff.execute() == 1 and sources == [True]
    assert synthetic.calls == [] and TOKEN not in capsys.readouterr().out


def test_source_exception_is_sanitized_without_retry(synthetic, monkeypatch, capsys):
    calls = []
    def fail(*args, **kwargs):
        calls.append(True)
        raise RuntimeError(TOKEN)
    monkeypatch.setattr(transport, "_run", fail)
    assert handoff.execute() == 1 and calls == [True]
    captured = capsys.readouterr()
    assert TOKEN not in captured.out and captured.err == ""
