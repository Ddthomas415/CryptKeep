"""Offline handoff verification. Tokens/native responses are always synthetic."""
import json
from pathlib import Path
import socket
from types import SimpleNamespace

import pytest

from docs.review_artifacts.companion_continuation_20261021 import execute_reviewed_continuation as handoff
from scripts.research import companion_cutover as cutover
from scripts.research import companion_docker_transport as transport
from scripts.research.companion_runtime_adapter import token_from_pipe


TOKEN = 'synthetic-continuation-token'


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError('native/network operation forbidden in offline test')
    monkeypatch.setattr(transport, '_run', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    common = handoff.helpers()
    source = SimpleNamespace(name='phase1-orchestrator', id='a' * 64, image='sha256:' + 'b' * 64)
    plan = SimpleNamespace(baseline=[source])
    continued = SimpleNamespace(execution_id='syntheticcontinuation01')
    argv = ['--synthetic-argument', 'fixture']
    calls = []
    monkeypatch.setattr(handoff, 'ROOT', tmp_path)
    monkeypatch.setattr(handoff, 'validated', lambda: (common, argv, plan, continued))
    monkeypatch.setattr(handoff.resource, 'setrlimit', lambda *a: None)
    monkeypatch.setattr(handoff.os, 'chdir', lambda *a: None)
    monkeypatch.setattr(transport.DockerTransport, '_verify_cli', lambda *a: True)
    def native(args, **kwargs):
        calls.append(('source', args, kwargs))
        assert args[-1] == source.id and common.source_format(source) in args
        assert kwargs == dict(timeout=10, input_bytes=None, limit=8192, env=dict(transport.ENV))
        return json.dumps('SERVICE_TOKEN=' + TOKEN).encode() + b'\n'
    monkeypatch.setattr(transport, '_run', native)
    def invoke(actual):
        calls.append(('consumer', actual))
        fd = int(actual[actual.index('--token-fd') + 1])
        assert token_from_pipe(fd) == TOKEN
        return 23
    monkeypatch.setattr(cutover, 'main', invoke)
    return SimpleNamespace(common=common, calls=calls, root=tmp_path, continued=continued, argv=argv)


def test_verified_legacy_helpers_are_reused_without_invoking_old_launcher():
    common = handoff.helpers()
    assert common.parse_token(b'"SERVICE_TOKEN=synthetic"') == 'synthetic'
    assert common.__name__ != '__main__'


def test_helper_drift_refuses_before_exec(monkeypatch):
    read = Path.read_bytes
    def changed(path):
        return b'raise AssertionError("must never execute")' if path.name == 'execute_reviewed_cutover.py' else read(path)
    monkeypatch.setattr(Path, 'read_bytes', changed)
    with pytest.raises(ValueError, match='reviewed_helper_changed'):
        handoff.helpers()


def test_frozen_actual_inputs_accept_only_unchanged_consumers():
    common = handoff.helpers()
    record = common.checked_json(handoff.HERE / 'runtime_packet/reviewed_continuation.json', handoff.CONTINUATION_SHA)
    changed = any(handoff.hashlib.sha256((handoff.ROOT / name).read_bytes()).hexdigest() != digest
                  for name, digest in record['consumer_sha256'].items())
    if changed:
        with pytest.raises(ValueError, match='reviewed_consumer_changed'):
            handoff.validated()
        return
    _, argv, plan, continued = handoff.validated()
    assert '--execute-cutover' not in argv and '--token-fd' not in argv
    assert continued.execution_id != plan.attempt
    assert continued.execution_id == 's3cutover20261022health01'


def test_default_calls_only_existing_inert_entrypoint(monkeypatch):
    seen = []
    monkeypatch.setattr(handoff, 'validated', lambda: (None, ['--synthetic-input'], None, None))
    def inert(argv):
        seen.append(argv)
        assert '--execute-cutover' not in argv and '--token-fd' not in argv
        return 0
    monkeypatch.setattr(cutover, 'main', inert)
    assert handoff.validate_only() == 0 and len(seen) == 1


def test_source_and_consumer_called_once_with_owned_private_pipe(synthetic, capsys):
    assert handoff.execute() == 23
    assert [call[0] for call in synthetic.calls] == ['source', 'consumer']
    assert TOKEN not in repr(synthetic.calls)
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('kind', ['directory', 'broken_symlink'])
def test_consumed_receipt_refuses_before_source_read(synthetic, capsys, kind):
    destination = synthetic.root.joinpath(*cutover.STATE_PARTS, synthetic.continued.execution_id)
    destination.parent.mkdir(parents=True)
    if kind == 'directory':
        destination.mkdir()
    else:
        destination.symlink_to(synthetic.root / 'absent')
    assert handoff.execute() == 1 and synthetic.calls == []
    result = json.loads(capsys.readouterr().out)
    assert result['entrypoint_handoff_entered'] is False


def test_cli_hash_refusal_reads_no_token(synthetic, monkeypatch, capsys):
    monkeypatch.setattr(transport.DockerTransport, '_verify_cli', lambda *a: False)
    assert handoff.execute() == 1 and synthetic.calls == []
    assert TOKEN not in capsys.readouterr().out


@pytest.mark.parametrize('raw', [b'', b'bad-json', b'"SERVICE_TOKEN="',
    b'"SERVICE_TOKEN=synthetic"\n"SERVICE_TOKEN=duplicate"', b'"SERVICE_TOKEN=has space"'])
def test_invalid_source_refuses_without_consumer(synthetic, monkeypatch, capsys, raw):
    calls = []
    monkeypatch.setattr(transport, '_run', lambda *a, **k: calls.append(True) or raw)
    assert handoff.execute() == 1
    assert calls == [True] and not any(call[0] == 'consumer' for call in synthetic.calls)
    assert TOKEN not in capsys.readouterr().out


def test_source_exception_is_sanitized_without_retry(synthetic, monkeypatch, capsys):
    calls = []
    def fail(*a, **k):
        calls.append(True)
        raise RuntimeError(TOKEN)
    monkeypatch.setattr(transport, '_run', fail)
    assert handoff.execute() == 1 and calls == [True]
    captured = capsys.readouterr()
    assert TOKEN not in captured.out and captured.err == ''


def test_consumer_drift_refuses_before_source_or_runtime(monkeypatch):
    read = Path.read_bytes
    def changed(path):
        return b'changed' if path.name == 'companion_cutover.py' else read(path)
    monkeypatch.setattr(Path, 'read_bytes', changed)
    with pytest.raises(ValueError, match='reviewed_consumer_changed'):
        handoff.validated()


def test_continuation_record_hash_drift_refuses(monkeypatch):
    read = Path.read_bytes
    def changed(path):
        return b'{}' if path.name == 'reviewed_continuation.json' else read(path)
    monkeypatch.setattr(Path, 'read_bytes', changed)
    with pytest.raises(ValueError, match='reviewed_input_changed'):
        handoff.validated()
