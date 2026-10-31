"""Offline entrypoint bridge: real staged controller, synthetic native/runtime state.

Input-loader bindings are tested separately in test_companion_cutover_inputs.py.
No test invokes the operational CLI, Docker, network or a real token reader.
"""
from dataclasses import replace
import fcntl
import inspect
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts.research import companion_cutover as entry
from scripts.research import companion_existing_controller as core
from scripts.research import companion_install_docker as native
from scripts.research import companion_installer as install
from tests.test_companion_staged_update import harness, reviewed, StagedRuntime


TOKEN = 'SYNTHETIC_TOKEN_DO_NOT_PRINT'
PRIVATE = ('SYNTHETIC_SECRET', TOKEN, 'SYNTHETIC_PRIVATE_PAYLOAD')


def forbidden(*args, **kwargs):
    raise AssertionError('offline test attempted native, network or repeated preparation work')


@pytest.fixture
def setup(tmp_path, monkeypatch):
    plan, backend, _, preparation = harness()
    result = preparation.prepare_staged(plan, authorized=True)
    assert result['state'] == 'READY_FOR_INDEPENDENT_REVIEW'
    prepared = reviewed(plan, result['preparation_evidence'])
    backend.calls.clear()
    root = tmp_path / 'repo'
    root.mkdir(mode=0o700)
    lock = tmp_path / 'shared-install.lock'
    assert entry.LOCK_PATH == entry.preparation.LOCK_PATH
    args = []
    for name in ('manifest', 'preparation-evidence', 'preparation-review', 'staged-metadata',
                 'runtime-review', 'topical-approvals', 'dependency-review'):
        path = tmp_path / (name + '.json')
        path.write_text('{}')  # Only the stubbed loader sees these dispatch inputs.
        args.extend(('--' + name, str(path)))
    for name in ('manifest', 'preparation-review', 'runtime-review'):
        args.extend(('--reviewed-' + name + '-sha256', 'a' * 64))
    pins = object()  # No policy approval is fabricated by the entrypoint fixture.
    runtime = StagedRuntime(backend)
    events, calls, runners, rollbacks, configs = [], [], [], [], []
    closed = []
    runtime.close = lambda: closed.append(True)

    class Inline:
        def call(self, fn, arguments, timeout):
            assert 0 < timeout <= 60
            calls.append((fn, arguments, timeout))
            return fn(*arguments)

    def load(arguments):
        events.append(('load', arguments))
        return plan, prepared, pins

    def token(fd, *, timeout):
        events.append(('token', fd, timeout))
        assert fd > 2 and timeout == 2
        os.close(fd)
        return TOKEN

    def transport(cli_sha256, config_dir, *, authorized):
        assert cli_sha256 == plan.cli_sha256 and authorized is True
        assert config_dir.is_absolute() and config_dir.is_dir()
        assert list(config_dir.iterdir()) == []
        configs.append(config_dir)
        events.append(('transport',))
        return SimpleNamespace(config_dir=config_dir)

    def runtime_factory(actual_transport, actual_pins, *, service_token, enabled):
        assert actual_pins is pins and service_token == TOKEN and enabled is True
        assert actual_transport.config_dir == configs[-1]
        events.append(('runtime',))
        return runtime

    def factory(actual_plan, actual_root, *, enabled):
        assert actual_plan == plan and actual_root == root and enabled is True
        events.append(('backend',))
        return backend

    run = install.Installer.run
    rollback = install.Installer._rollback

    def dispatch(self, actual_plan, **kwargs):
        assert actual_plan == plan
        assert kwargs == dict(authorized=True, runtime=runtime, startup_authorized=True, prepared=prepared)
        runners.append(self)
        return run(self, actual_plan, **kwargs)

    def recover(self):
        assert self.recovering is True
        rollbacks.append(self)
        return rollback(self)

    handlers = {signal.SIGINT: object(), signal.SIGTERM: object()}
    original_handlers = dict(handlers)

    def signal_handler(sig, handler):
        previous = handlers[sig]
        handlers[sig] = handler
        events.append(('signal', sig))
        return previous

    monkeypatch.setattr(entry, 'ROOT', root)
    monkeypatch.setattr(entry, 'LOCK_PATH', lock)
    monkeypatch.setattr(entry, 'load_inputs', load)
    monkeypatch.setattr(entry, 'DockerInstallBackend', factory)
    monkeypatch.setattr(entry, 'DockerTransport', transport)
    monkeypatch.setattr(entry.adapter, 'PinnedRuntimeAdapter', runtime_factory)
    monkeypatch.setattr(entry.adapter, 'token_from_pipe', token)
    monkeypatch.setattr(entry.signal, 'signal', signal_handler)
    monkeypatch.setattr(core, 'ProcessExecutor', Inline)
    monkeypatch.setattr(install.Installer, 'run', dispatch)
    monkeypatch.setattr(install.Installer, '_rollback', recover)
    monkeypatch.setattr(install.Installer, 'prepare_staged', forbidden)
    monkeypatch.setattr(native.DockerInstallBackend, '_command', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    return SimpleNamespace(plan=plan, backend=backend, prepared=prepared, runtime=runtime, pins=pins,
        root=root, lock=lock, args=args, events=events, calls=calls, runners=runners, rollbacks=rollbacks,
        configs=configs, closed=closed, handlers=handlers, original_handlers=original_handlers,
        directory=root.joinpath(*entry.STATE_PARTS, plan.attempt))


def invoke(setup, capsys, *, execute=True, token_fd=None):
    args = list(setup.args)
    owned = None
    if execute:
        args.append('--execute-cutover')
        if token_fd is None:
            owned, writer = os.pipe()  # Empty local fixture descriptor; no credential read.
            os.close(writer)
            token_fd = owned
    if token_fd is not None:
        args.extend(('--token-fd', str(token_fd)))
    try:
        code = entry.main(args)
    finally:
        if owned is not None:
            try:
                os.close(owned)
            except OSError:
                pass
    captured = capsys.readouterr()
    assert captured.err == '' and len(captured.out.splitlines()) == 1
    assert all(secret not in captured.out for secret in PRIVATE)
    return code, json.loads(captured.out)


def assert_no_dispatch(setup):
    assert not setup.backend.calls and not setup.runners and not setup.calls
    assert not any(e[0] in {'token', 'transport', 'runtime', 'backend', 'signal'} for e in setup.events)


def assert_restored(setup):
    assert all(setup.backend.rows[r.name] == r for r in setup.plan.baseline[:3])
    assert all(setup.backend.rows[r.name].id == r.id and setup.backend.rows[r.name].state == 'running'
               for r in setup.plan.baseline[3:])
    assert not any(row.attempt for row in setup.backend.rows.values())


def test_default_is_input_validation_only_no_lock_dirs_token_or_native(setup, capsys, monkeypatch):
    monkeypatch.setattr(entry, '_reserve', forbidden)
    monkeypatch.setattr(entry.fcntl, 'flock', forbidden)
    code, summary = invoke(setup, capsys, execute=False)
    assert code == 0 and summary['state'] == 'READY_FOR_INDEPENDENT_REVIEW'
    assert summary['actions_executed'] is False and summary['startup_authorized'] is False
    assert summary['input_bindings_validated'] is True
    assert summary['controller_budget_seconds'] == 600 and summary['recovery_reserve_seconds'] == 180
    assert not setup.lock.exists() and list(setup.root.iterdir()) == []
    assert_no_dispatch(setup)


def test_token_fd_in_default_refuses_without_reading_or_closing_it(setup, capsys):
    fd, writer = os.pipe()
    os.close(writer)
    try:
        code, summary = invoke(setup, capsys, execute=False, token_fd=fd)
        assert code == 1 and summary['failure_phase'] == 'input_validation'
        os.fstat(fd)
        assert setup.events == [] and not setup.lock.exists()
        assert_no_dispatch(setup)
    finally:
        os.close(fd)


@pytest.mark.parametrize('fd', [-1, 0, 1, 2])
def test_standard_or_invalid_token_descriptors_refused_before_loader(setup, capsys, fd):
    code, summary = invoke(setup, capsys, token_fd=fd)
    assert code == 1 and summary['failure_phase'] == 'input_validation'
    assert setup.events == [] and not setup.lock.exists()
    assert_no_dispatch(setup)


@pytest.mark.parametrize('execute', [False, True])
def test_input_loader_hash_or_binding_refusal_is_sanitized_and_inert(setup, capsys, monkeypatch, execute):
    def reject(args):
        raise ValueError('SYNTHETIC_SECRET invalid hash or missing policy approval')
    monkeypatch.setattr(entry, 'load_inputs', reject)
    code, summary = invoke(setup, capsys, execute=execute)
    assert code == 1 and summary['failure_phase'] == 'input_validation'
    assert summary['reason'] == 'cutover_refused'
    assert not setup.lock.exists() and not setup.directory.exists()
    assert_no_dispatch(setup)


@pytest.mark.parametrize('option', ['--runtime-review', '--reviewed-runtime-review-sha256',
                                   '--dependency-review', '--topical-approvals', '--staged-metadata'])
def test_required_policy_inputs_cannot_be_omitted_even_in_default(setup, capsys, option):
    args = list(setup.args)
    index = args.index(option)
    del args[index:index + 2]
    with pytest.raises(SystemExit) as exc:
        entry.main(args)
    assert exc.value.code == 2
    capsys.readouterr()
    assert not setup.events and not setup.lock.exists()
    assert_no_dispatch(setup)


def test_busy_shared_install_lock_refuses_before_token_or_reservation(setup, capsys):
    fd = os.open(setup.lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        code, summary = invoke(setup, capsys)
        assert code == 1 and summary['failure_phase'] == 'lock'
        assert not setup.directory.exists()
        assert_no_dispatch(setup)
    finally:
        os.close(fd)


@pytest.mark.parametrize('kind', ['symlink', 'permissions', 'owner'])
def test_unsafe_lock_refused_before_dispatch(setup, capsys, monkeypatch, kind):
    target = setup.root.parent / 'untouched'
    target.write_bytes(b'untouched')
    if kind == 'symlink':
        setup.lock.symlink_to(target)
    else:
        setup.lock.touch(mode=0o600)
        if kind == 'permissions':
            setup.lock.chmod(0o644)
        else:
            uid = os.geteuid()
            monkeypatch.setattr(entry.os, 'geteuid', lambda: uid + 1)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['failure_phase'] == 'lock'
    assert target.read_bytes() == b'untouched'
    assert_no_dispatch(setup)


@pytest.mark.parametrize('index', range(5))
def test_symlink_root_ancestor_or_attempt_never_followed(setup, capsys, monkeypatch, index):
    outside = setup.root.parent / 'outside'
    outside.mkdir(mode=0o700)
    parts = [*entry.STATE_PARTS, setup.plan.attempt]
    if index == 4:
        link = setup.root.parent / 'linked-root'
        link.symlink_to(setup.root, target_is_directory=True)
        monkeypatch.setattr(entry, 'ROOT', link)
    else:
        parent = setup.root.joinpath(*parts[:index])
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        parent.joinpath(parts[index]).symlink_to(outside, target_is_directory=True)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['failure_phase'] == 'reservation'
    assert list(outside.iterdir()) == []
    assert_no_dispatch(setup)


def test_success_dispatches_once_with_existing_ids_and_public_artifacts(setup, capsys):
    code, summary = invoke(setup, capsys)
    assert code == 0 and summary['state'] == 'READY_FOR_INDEPENDENT_REVIEW'
    assert summary['running_update_complete'] is True and summary['query_passed'] is True
    assert summary['prepared_ids_preserved'] is True and summary['actions_executed'] is True
    assert summary['attempt_reserved'] is True
    assert len(setup.runners) == 1 and not setup.rollbacks
    assert setup.runners[0].end - setup.runners[0].work_end == 180
    assert [e[0] for e in setup.events if e[0] in {'load', 'token', 'transport', 'runtime', 'backend'}] == [
        'load', 'token', 'transport', 'runtime', 'backend']
    methods = [m for m, _ in setup.backend.calls]
    assert not set(methods).intersection({'build', 'create', 'create_staged'})
    assert methods.count('runtime_explain') == 1 and methods.count('runtime_start') == 4
    assert {setup.backend.rows[n].id for n in install.APPS} == {r.id for r in setup.prepared.replacements}
    assert all(setup.backend.rows[r.name] == r for r in setup.plan.baseline[:3])
    receipt = setup.directory / 'receipt.jsonl'
    provisional = setup.directory / 'provisional_result.json'
    assert summary['receipt'] == str(receipt)
    for path in (receipt, provisional, setup.lock):
        assert stat.S_ISREG(path.lstat().st_mode) and stat.S_IMODE(path.stat().st_mode) == 0o600
    for path in (setup.root.joinpath(*entry.STATE_PARTS[:i]) for i in range(1, 4)):
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
    assert stat.S_IMODE(setup.directory.stat().st_mode) == 0o700
    payload = json.loads(provisional.read_bytes())
    assert provisional.read_bytes() == install.canonical(payload)
    assert payload['provisional'] is True and 'installation_evidence' not in payload['result']
    assert not {'decision', 'reviewer', 'approval'}.intersection(payload)
    events = [json.loads(line) for line in receipt.read_text().splitlines()]
    assert events[-1]['phase'] == 'cutover_result_committed'
    for path in (receipt, provisional):
        assert all(secret not in path.read_text() for secret in PRIVATE)
    publications = [call for call in setup.calls if call[0] is entry._publish]
    assert len(publications) == 1 and 0 < publications[0][2] <= 2
    assert setup.closed == [True] and all(not path.exists() for path in setup.configs)
    assert setup.handlers == setup.original_handlers


@pytest.mark.parametrize('failure', [False, True])
def test_attempt_cannot_replay_after_success_or_failure_with_changed_hash_or_new_receipt(setup, capsys, monkeypatch, failure):
    if failure:
        setup.runtime.health_result[install.APPS[0]] = False
    assert invoke(setup, capsys)[0] == (1 if failure else 0)
    receipt = setup.directory / 'receipt.jsonl'
    receipt.rename(setup.directory / 'old-receipt.jsonl')
    changed = replace(setup.plan, manifest_sha256='f' * 64)
    monkeypatch.setattr(entry, 'load_inputs', lambda args: (changed, setup.prepared, setup.pins))
    previous_calls = len(setup.backend.calls)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['failure_phase'] == 'reservation'
    assert len(setup.runners) == 1 and len(setup.backend.calls) == previous_calls
    assert not receipt.exists() and (setup.directory / 'old-receipt.jsonl').is_file()
    if failure:
        assert_restored(setup)


@pytest.mark.parametrize('partial', [False, True])
def test_publication_failure_rolls_back_once_and_preserves_failed_artifacts(setup, capsys, monkeypatch, partial):
    publish = entry._publish
    def fail(fd, raw):
        if partial:
            assert publish(fd, raw) is True
        raise OSError('SYNTHETIC_SECRET publication failure')
    monkeypatch.setattr(entry, '_publish', fail)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['failure_phase'] == 'result_publication'
    assert summary['rollback_verified'] is True and summary['running_update_complete'] is False
    assert len(setup.runners) == len(setup.rollbacks) == 1
    assert_restored(setup)
    assert sum(m == 'runtime_explain' for m, _ in setup.backend.calls) == 1
    assert (setup.directory / 'provisional_result.json').exists() is partial
    receipt = setup.directory / 'receipt.jsonl'
    assert receipt.is_file() and all(secret not in receipt.read_text() for secret in PRIVATE)
    assert not any(json.loads(line)['phase'] == 'cutover_result_committed' for line in receipt.read_text().splitlines())
    assert setup.closed == [True] and setup.handlers == setup.original_handlers


def test_publication_budget_exhaustion_uses_recovery_reserve_without_publishing(setup, capsys, monkeypatch):
    run = install.Installer.run
    def expired(self, plan, **kwargs):
        result = run(self, plan, **kwargs)
        assert result['running_update_complete'] is True
        self.work_end = self.clock() - 1
        return result
    monkeypatch.setattr(install.Installer, 'run', expired)
    monkeypatch.setattr(entry, '_publish', forbidden)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['rollback_verified'] is True
    assert len(setup.rollbacks) == 1 and not (setup.directory / 'provisional_result.json').exists()
    assert not any(fn is forbidden for fn, _, _ in setup.calls)
    assert_restored(setup)


@pytest.mark.parametrize('sig', [signal.SIGINT, signal.SIGTERM])
def test_interrupt_after_starts_recovers_and_repeated_signal_does_not_reenter(setup, capsys, monkeypatch, sig):
    effect = setup.backend.effect
    interrupted, repeated = [], []
    def operation(method, fn, *args):
        if method == 'runtime_health' and not interrupted:
            interrupted.append(True)
            setup.handlers[sig](sig, None)
        if method == 'quiesce_replacement':
            repeated.append(True)
            setup.handlers[sig](sig, None)
        return effect(method, fn, *args)
    monkeypatch.setattr(setup.backend, 'effect', operation)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['rollback_verified'] is True
    assert interrupted and repeated and len(setup.rollbacks) == 1
    assert not (setup.directory / 'provisional_result.json').exists()
    assert setup.closed == [True] and setup.handlers == setup.original_handlers
    assert_restored(setup)


def test_final_receipt_failure_after_publication_recovers_and_does_not_commit(setup, capsys, monkeypatch):
    write = core.Receipt.write
    def broken(self, event):
        if event.get('phase') == 'cutover_result_committed':
            raise OSError('SYNTHETIC_SECRET commit failure')
        return write(self, event)
    monkeypatch.setattr(core.Receipt, 'write', broken)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['failure_phase'] == 'receipt_commit'
    assert summary['rollback_verified'] is True and summary['receipt_complete'] is False
    assert (setup.directory / 'provisional_result.json').is_file()
    events = [json.loads(line) for line in (setup.directory / 'receipt.jsonl').read_text().splitlines()]
    assert not any(e['phase'] == 'cutover_result_committed' for e in events)
    assert len(setup.rollbacks) == 1
    assert_restored(setup)


def test_unexpected_recovery_error_is_incomplete_not_a_traceback_or_false_success(setup, capsys, monkeypatch):
    monkeypatch.setattr(entry, '_publish', lambda *args: False)
    def broken(self):
        raise RuntimeError('SYNTHETIC_SECRET recovery error')
    monkeypatch.setattr(install.Installer, '_rollback', broken)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['state'] == 'INCOMPLETE'
    assert summary['rollback_verified'] is False and summary['running_update_complete'] is False
    assert setup.closed == [True] and setup.handlers == setup.original_handlers


@pytest.mark.parametrize('sig', [signal.SIGINT, signal.SIGTERM])
@pytest.mark.parametrize('boundary', ['partial_initialize', 'failure_handoff'])
def test_cancellation_at_initialization_and_exception_handoff_is_sanitized(setup, capsys, monkeypatch, sig, boundary):
    fired = []
    if boundary == 'failure_handoff':
        def fail(*args):
            raise OSError('SYNTHETIC_SECRET publication failure')
        monkeypatch.setattr(entry, '_publish', fail)
        code = entry.main.__code__
        lines, start = inspect.getsourcelines(entry.main)
        target = start + next(i for i, line in enumerate(lines) if 'if (runner is not None and runner.used' in line)
    else:
        code = install.Installer._initialize.__code__
        lines, start = inspect.getsourcelines(install.Installer._initialize)
        target = start + next(i for i, line in enumerate(lines) if 'self.plan, self.images =' in line)
    def trace(frame, event, arg):
        if event == 'line' and frame.f_code is code and frame.f_lineno == target and not fired:
            fired.append(True)
            sys.settrace(None)
            setup.handlers[sig](sig, None)
        return trace
    previous = sys.gettrace()
    try:
        sys.settrace(trace)
        status, summary = invoke(setup, capsys)
    finally:
        sys.settrace(previous)
    assert fired and status == 1 and summary['state'] == 'INCOMPLETE'
    assert setup.closed == [True] and setup.handlers == setup.original_handlers
    if boundary == 'failure_handoff':
        assert summary['rollback_verified'] is True and len(setup.rollbacks) == 1
        assert_restored(setup)
    else:
        assert not setup.rollbacks and not setup.backend.calls
        assert all(setup.backend.rows[r.name] == r for r in setup.plan.baseline)


def test_new_directory_entries_are_parent_fsynced_before_token_or_native(setup, capsys, monkeypatch):
    mkdir, fsync, token = entry.os.mkdir, entry.os.fsync, entry.adapter.token_from_pipe
    events = []
    def create(part, *args, **kwargs):
        result = mkdir(part, *args, **kwargs)
        events.append(('mkdir', os.fstat(kwargs['dir_fd']).st_ino, str(part)))
        return result
    def sync(fd):
        events.append(('fsync', os.fstat(fd).st_ino))
        return fsync(fd)
    def read_token(*args, **kwargs):
        events.append(('token',))
        return token(*args, **kwargs)
    monkeypatch.setattr(entry.os, 'mkdir', create)
    monkeypatch.setattr(entry.os, 'fsync', sync)
    monkeypatch.setattr(entry.adapter, 'token_from_pipe', read_token)
    # tempfile also uses os.mkdir, after the reservation has been verified.
    original_create = create
    def any_directory(part, *args, **kwargs):
        return original_create(part, *args, **kwargs) if 'dir_fd' in kwargs else mkdir(part, *args, **kwargs)
    monkeypatch.setattr(entry.os, 'mkdir', any_directory)
    assert invoke(setup, capsys)[0] == 0
    end = events.index(('token',))
    positions = [i for i, event in enumerate(events[:end]) if event[0] == 'mkdir']
    assert [events[i][2] for i in positions] == [*entry.STATE_PARTS, setup.plan.attempt]
    for offset, position in enumerate(positions):
        next_position = positions[offset + 1] if offset + 1 < len(positions) else end
        assert ('fsync', events[position][1]) in events[position + 1:next_position]


@pytest.mark.parametrize('barrier', [1, 2, 3, 4])
def test_failed_directory_fsync_prevents_dispatch(setup, capsys, monkeypatch, barrier):
    fsync = entry.os.fsync
    count = [0]
    def fail(fd):
        count[0] += 1
        if count[0] == barrier:
            raise OSError('SYNTHETIC_SECRET durability failure')
        return fsync(fd)
    monkeypatch.setattr(entry.os, 'fsync', fail)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['failure_phase'] == 'reservation'
    assert summary['attempt_reserved'] is None
    assert_no_dispatch(setup)
