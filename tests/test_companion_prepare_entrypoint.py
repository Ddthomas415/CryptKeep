"""Offline preparation entrypoint proof using real files and a synthetic backend."""
import fcntl
import hashlib
import json
import os
import socket
import stat
import subprocess
from types import SimpleNamespace

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_install_docker as native
from scripts.research import companion_installer as install
from scripts.research import companion_prepare as entry
from scripts.research import companion_staged_update as staged
from tests.test_companion_installer import configured_manifest
from tests.test_companion_running_storage import running_manifest
from tests.test_companion_staged_update import Backend, reviewed


def forbidden(*args, **kwargs):
    raise AssertionError('offline preparation must not invoke native/startup operations')


@pytest.fixture
def setup(tmp_path, monkeypatch):
    root = tmp_path / 'repo'
    root.mkdir(mode=0o700)
    lock = tmp_path / 'shared-install.lock'
    manifest_path = tmp_path / 'manifest.json'
    data = running_manifest()
    data['schema'] = 'companion-staged-update-v5'
    raw = install.canonical(data)
    manifest_path.write_bytes(raw)
    trusted = hashlib.sha256(raw).hexdigest()
    plan = install.Plan.load(raw, trusted)
    backends, executor_calls = [], []
    failure = {'method': None, 'after': False}

    class Inline:
        def call(self, fn, args, timeout):
            assert 0 < timeout <= 60
            executor_calls.append((fn, args, timeout))
            return fn(*args)

    def factory(actual_plan, actual_root, *, enabled):
        assert actual_plan == plan and actual_root == root and enabled is True
        backend = Backend(actual_plan, fail=failure['method'], after=failure['after'])
        backends.append(backend)
        return backend

    monkeypatch.setattr(entry, 'ROOT', root)
    monkeypatch.setattr(entry, 'LOCK_PATH', lock)
    monkeypatch.setattr(entry, 'DockerInstallBackend', factory)
    monkeypatch.setattr(core, 'ProcessExecutor', Inline)
    monkeypatch.setattr(install.Installer, 'run', forbidden)
    monkeypatch.setattr(native.DockerInstallBackend, '_command', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    return SimpleNamespace(root=root, lock=lock, manifest=manifest_path, plan=plan,
        trusted=trusted, backends=backends, failure=failure, executor_calls=executor_calls,
        directory=root / '.cbp_state/runtime/companion_preparations' / plan.attempt)


def invoke(setup, capsys, *, execute=True, trusted=None):
    args = ['--manifest', str(setup.manifest), '--reviewed-manifest-sha256',
            setup.trusted if trusted is None else trusted]
    if execute:
        args.append('--execute-preparation')
    code = entry.main(args)
    captured = capsys.readouterr()
    assert captured.err == ''
    assert 'SYNTHETIC_SECRET' not in captured.out
    assert len(captured.out.splitlines()) == 1
    return code, json.loads(captured.out)


def unchanged_originals(setup):
    backend = setup.backends[-1]
    assert all(backend.rows[row.name] == row for row in setup.plan.baseline)
    methods = [method for method, _ in backend.calls]
    assert not set(methods).intersection({'quiesce', 'restart_original', 'rename', 'disconnect',
        'connect', 'create', 'runtime_start', 'runtime_health', 'runtime_explain', 'runtime_storage',
        'rename_staged', 'disconnect_staged', 'connect_staged', 'quiesce_replacement'})


def test_default_validates_only_without_lock_directory_backend_or_executor(setup, capsys, monkeypatch):
    monkeypatch.setattr(entry, '_reserve', forbidden)
    monkeypatch.setattr(entry.fcntl, 'flock', forbidden)
    code, summary = invoke(setup, capsys, execute=False)
    assert code == 0 and summary['state'] == 'READY_FOR_INDEPENDENT_REVIEW'
    assert summary['actions_executed'] is False and summary['startup_authorized'] is False
    assert summary['manifest_sha256'] == setup.trusted
    assert summary['output_directory'] == str(setup.directory)
    assert summary['controller_budget_seconds'] == 300
    assert summary['recovery_reserve_seconds'] == 120
    assert not setup.lock.exists() and list(setup.root.iterdir()) == []
    assert setup.backends == [] and setup.executor_calls == []


@pytest.mark.parametrize('execute', [False, True])
@pytest.mark.parametrize('trusted', ['0' * 64, 'not-a-hash'])
def test_wrong_hash_is_sanitized_and_inert(setup, capsys, execute, trusted):
    code, summary = invoke(setup, capsys, execute=execute, trusted=trusted)
    assert code == 1 and summary['state'] == 'INCOMPLETE'
    assert summary['reason'] == 'preparation_refused'
    assert not setup.lock.exists() and not setup.directory.exists()
    assert not setup.backends and not setup.executor_calls


@pytest.mark.parametrize('profile', ['configured', 'running'])
def test_valid_non_v5_profiles_are_refused_before_lock(setup, capsys, profile):
    data = configured_manifest() if profile == 'configured' else running_manifest()
    raw = install.canonical(data)
    trusted = hashlib.sha256(raw).hexdigest()
    assert not install.Plan.load(raw, trusted).staged
    setup.manifest.write_bytes(raw)
    code, summary = invoke(setup, capsys, trusted=trusted)
    assert code == 1 and summary['reason'] == 'preparation_refused'
    assert not setup.lock.exists() and not setup.backends
    assert not setup.directory.exists()


def test_busy_shared_lock_refuses_without_reservation(setup, capsys):
    fd = os.open(setup.lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        code, summary = invoke(setup, capsys)
        assert code == 1 and summary['attempt_reserved'] is False
        assert not setup.directory.exists() and not setup.backends
    finally:
        os.close(fd)


@pytest.mark.parametrize('kind', ['symlink', 'permissions', 'directory', 'owner'])
def test_unsafe_lock_refuses_before_backend(setup, capsys, monkeypatch, kind):
    if kind == 'symlink':
        target = setup.root.parent / 'lock-target'
        target.write_bytes(b'untouched')
        setup.lock.symlink_to(target)
    elif kind == 'directory':
        setup.lock.mkdir(mode=0o700)
    else:
        setup.lock.touch(mode=0o600)
        if kind == 'permissions':
            setup.lock.chmod(0o644)
        else:
            owner = os.geteuid()
            monkeypatch.setattr(entry.os, 'geteuid', lambda: owner + 1)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['reason'] == 'preparation_refused'
    assert not setup.directory.exists() and not setup.backends
    if kind == 'symlink':
        assert target.read_bytes() == b'untouched'


@pytest.mark.parametrize('part', ['root', '.cbp_state', 'runtime', 'companion_preparations', 'attempt'])
def test_symlink_directory_components_are_never_followed(setup, capsys, monkeypatch, part):
    outside = setup.root.parent / 'outside'
    outside.mkdir(mode=0o700)
    if part == 'root':
        link = setup.root.parent / 'root-link'
        link.symlink_to(setup.root, target_is_directory=True)
        monkeypatch.setattr(entry, 'ROOT', link)
    else:
        parts = ['.cbp_state', 'runtime', 'companion_preparations', setup.plan.attempt]
        index = 3 if part == 'attempt' else parts.index(part)
        parent = setup.root.joinpath(*parts[:index])
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        parent.joinpath(parts[index]).symlink_to(outside, target_is_directory=True)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['reason'] == 'preparation_refused'
    assert not setup.backends and list(outside.iterdir()) == []


def test_success_publishes_plain_canonical_reviewable_evidence_and_real_receipt(setup, capsys):
    code, summary = invoke(setup, capsys)
    assert code == 0 and summary['state'] == 'READY_FOR_INDEPENDENT_REVIEW'
    assert summary['preparation_complete'] is True and summary['actions_executed'] is True
    assert summary['startup_authorized'] is False and summary['services_started'] is False
    assert summary['originals_interrupted'] is False and summary['attempt_reserved'] is True
    assert set(summary) == {'state', 'preparation_complete', 'actions_executed', 'startup_authorized',
        'services_started', 'originals_interrupted', 'attempt_reserved', 'receipt', 'evidence',
        'evidence_sha256', 'manifest_sha256'}
    assert issubclass(entry.PreparationReceipt, core.Receipt)
    evidence = setup.directory / 'evidence.json'
    receipt = setup.directory / 'receipt.jsonl'
    assert summary['evidence'] == str(evidence) and summary['receipt'] == str(receipt)
    for path in (evidence, receipt, setup.lock):
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
        assert info.st_uid == os.geteuid()
    raw = evidence.read_bytes()
    payload = json.loads(raw)
    assert raw == install.canonical(payload)
    assert hashlib.sha256(raw).hexdigest() == summary['evidence_sha256']
    assert payload['manifest_sha256'] == setup.trusted
    assert 'decision' not in payload and 'reviewer' not in payload
    approval = reviewed(setup.plan, payload)
    assert isinstance(approval, staged.ReviewedPreparation)
    assert len(approval.replacements) == 4
    assert {row.id for row in approval.replacements} == {
        row.id for row in setup.backends[0].rows.values() if row.attempt == setup.plan.attempt}
    assert all(row.state == 'created' and row.started in core.NEVER_STARTED for row in approval.replacements)
    events = [json.loads(line) for line in receipt.read_text().splitlines()]
    assert events and 'SYNTHETIC_SECRET' not in receipt.read_text()
    unchanged_originals(setup)
    calls = [name for name, _ in setup.backends[0].calls]
    assert calls.count('prepare') == 1 and calls.count('build') == 4
    assert calls.count('create_staged') == 4 and calls.count('verify_staged_sources') == 4
    publications = [call for call in setup.executor_calls if call[0] is entry._publish]
    assert len(publications) == 1 and 0 < publications[0][2] <= 2
    assert publications[0][1][1] == raw


@pytest.mark.parametrize('failed', [False, True])
def test_attempt_cannot_replay_even_with_new_receipt_name(setup, capsys, failed):
    if failed:
        setup.failure['method'] = 'build'
    code, _ = invoke(setup, capsys)
    assert code == (1 if failed else 0) and setup.directory.is_dir()
    receipt = setup.directory / 'receipt.jsonl'
    receipt.rename(setup.directory / 'first-receipt.jsonl')
    setup.failure['method'] = None
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['reason'] == 'preparation_refused'
    assert len(setup.backends) == 1 and not receipt.exists()
    assert (setup.directory / 'first-receipt.jsonl').exists()
    unchanged_originals(setup)


@pytest.mark.parametrize('method', ['build', 'verify_staged_sources'])
def test_failed_preparation_consumes_attempt_and_preserves_originals(setup, capsys, method):
    setup.failure['method'] = method
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['attempt_reserved'] is True
    assert summary['cleanup_verified'] is True and setup.directory.is_dir()
    assert (setup.directory / 'receipt.jsonl').is_file()
    assert not (setup.directory / 'evidence.json').exists()
    assert not any(row.attempt for row in setup.backends[0].rows.values())
    unchanged_originals(setup)


@pytest.mark.parametrize('partial', [False, True])
def test_publication_failure_cleans_acknowledged_stages_and_keeps_failed_artifacts(setup, capsys, monkeypatch, partial):
    publish = entry._publish

    def fail(directory_fd, raw):
        if partial:
            assert publish(directory_fd, raw) is True
        raise OSError('SYNTHETIC_SECRET publication denied')

    monkeypatch.setattr(entry, '_publish', fail)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['attempt_reserved'] is True
    assert summary['cleanup_verified'] is True
    assert not any(row.attempt for row in setup.backends[0].rows.values())
    assert (setup.directory / 'receipt.jsonl').is_file()
    assert (setup.directory / 'evidence.json').exists() is partial
    removals = [args for method, args in setup.backends[0].calls if method == 'remove_staged']
    assert len(removals) == 4
    unchanged_originals(setup)
    before = len(setup.backends)
    assert invoke(setup, capsys)[0] == 1 and len(setup.backends) == before


def test_expired_work_deadline_skips_publication_and_uses_cleanup_reserve(setup, capsys, monkeypatch):
    prepare = install.Installer.prepare_staged

    def expired(self, plan, *, authorized=False):
        result = prepare(self, plan, authorized=authorized)
        assert result['state'] == 'READY_FOR_INDEPENDENT_REVIEW'
        self.work_end = self.clock() - 1
        return result

    monkeypatch.setattr(install.Installer, 'prepare_staged', expired)
    monkeypatch.setattr(entry, '_publish', forbidden)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['cleanup_verified'] is True
    assert not any(fn is forbidden for fn, _, _ in setup.executor_calls)
    assert not (setup.directory / 'evidence.json').exists()
    assert not any(row.attempt for row in setup.backends[0].rows.values())
    unchanged_originals(setup)


def test_publication_timeout_is_capped_by_remaining_work_budget(setup, capsys, monkeypatch):
    prepare = install.Installer.prepare_staged

    def nearly_expired(self, plan, *, authorized=False):
        result = prepare(self, plan, authorized=authorized)
        self.work_end = self.clock() + 0.25
        return result

    monkeypatch.setattr(install.Installer, 'prepare_staged', nearly_expired)
    code, _ = invoke(setup, capsys)
    assert code == 0
    calls = [call for call in setup.executor_calls if call[0] is entry._publish]
    assert len(calls) == 1 and 0 < calls[0][2] <= 0.25


def test_lost_creation_ack_reports_stage_and_unresolved_resource(setup, capsys):
    setup.failure.update(method='create_staged', after=True)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['cleanup_verified'] is False
    assert summary['failure_phase'] == 'preparation'
    assert summary['preparation_failure_stage'] == 'staged_creation'
    assert summary['unresolved_creation'] == [install.APPS[0]]
    assert summary['unresolved_cleanup'] == []
    assert sum(bool(row.attempt) for row in setup.backends[0].rows.values()) == 1
    receipt = setup.directory / 'receipt.jsonl'
    assert summary['receipt'] == str(receipt)
    last = json.loads(receipt.read_text().splitlines()[-1])
    assert last['phase'] == 'preparation_entrypoint_failed'
    assert last['installation_evidence']['unresolved_creation'] == [install.APPS[0]]
    unchanged_originals(setup)


@pytest.mark.parametrize('after', [False, True])
def test_publication_cleanup_uncertainty_is_visible(setup, capsys, monkeypatch, after):
    setup.failure.update(method='remove_staged', after=after)
    def fail(*args):
        raise OSError('SYNTHETIC_SECRET')
    monkeypatch.setattr(entry, '_publish', fail)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['cleanup_verified'] is False
    assert summary['failure_phase'] == 'evidence_publication'
    assert summary['unresolved_creation'] == []
    assert summary['unresolved_cleanup'] == [install.APPS[-1]]
    unchanged_originals(setup)


def test_new_directory_entries_have_parent_fsync_before_backend(setup, capsys, monkeypatch):
    mkdir, fsync, factory = entry.os.mkdir, entry.os.fsync, entry.DockerInstallBackend
    events = []
    def create(part, *args, **kwargs):
        result = mkdir(part, *args, **kwargs)
        events.append(('mkdir', os.fstat(kwargs['dir_fd']).st_ino, str(part)))
        return result
    def sync(fd):
        events.append(('fsync', os.fstat(fd).st_ino))
        return fsync(fd)
    def backend(*args, **kwargs):
        events.append(('backend',))
        return factory(*args, **kwargs)
    monkeypatch.setattr(entry.os, 'mkdir', create)
    monkeypatch.setattr(entry.os, 'fsync', sync)
    monkeypatch.setattr(entry, 'DockerInstallBackend', backend)
    assert invoke(setup, capsys)[0] == 0
    end = events.index(('backend',))
    created = [i for i, event in enumerate(events[:end]) if event[0] == 'mkdir']
    assert [events[i][2] for i in created] == [*entry.STATE_PARTS, setup.plan.attempt]
    for offset, position in enumerate(created):
        next_entry = created[offset + 1] if offset + 1 < len(created) else end
        assert ('fsync', events[position][1]) in events[position + 1:next_entry]


@pytest.mark.parametrize('barrier', [1, 2, 3, 4])
def test_failed_ancestor_or_marker_barrier_prevents_native_work(setup, capsys, monkeypatch, barrier):
    fsync = entry.os.fsync
    count = [0]
    def fail(fd):
        count[0] += 1
        if count[0] == barrier:
            raise OSError('SYNTHETIC_SECRET')
        return fsync(fd)
    monkeypatch.setattr(entry.os, 'fsync', fail)
    code, summary = invoke(setup, capsys)
    assert code == 1 and summary['failure_phase'] == 'reservation'
    assert summary['attempt_reserved'] is None
    assert summary['unresolved_creation'] == summary['unresolved_cleanup'] == []
    assert not setup.backends and not setup.executor_calls
