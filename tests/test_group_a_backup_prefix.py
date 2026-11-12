"""Active journal/shared CAS recovery on synthetic producer data only."""
import fcntl
import hashlib
import io
import json
import os
import threading
import time

import pytest

from services.control import group_a_backup_bundle as core
from services.control import group_a_backup_prefix as prefix
from tests.test_group_a_backup_acquisition import setup, encoded


def run(setup, **kwargs):
    return prefix.acquire_prefix_bundle(
        setup['output'], release='fixture1', bundle_id='batch0001',
        accounts=setup['sources'], public_configurations=setup['configs'],
        public_run_manifest={'release': 'fixture1', 'source_sha256': 'a' * 64},
        limits=kwargs.pop('limits', core.BundleLimits(500, 40_000_000, 5_000_000)),
        deadline=kwargs.pop('deadline', time.monotonic() + 20), **kwargs,
    )


def capture(setup, monkeypatch, *, index=0, shared=None, loop=1):
    from services.strategies import signal_input_capture as producer
    from tests.test_runner_decision_capture import make_record
    root = setup['sources'][index].data_directory
    monkeypatch.setenv('CBP_CAPTURE_RUNNER_DECISIONS', '1')
    if shared is None:
        monkeypatch.delenv('CBP_RUNNER_DECISION_OBJECT_DIR', raising=False)
    else:
        monkeypatch.setenv('CBP_RUNNER_DECISION_OBJECT_DIR', str(shared))
    monkeypatch.setattr(producer, 'data_dir', lambda: root)
    monkeypatch.setattr(producer, '_runner_commit_identity', lambda: 'a' * 40)
    record = make_record()
    record['loop'] = loop
    result = producer.capture_runner_decision(record)
    assert result['status'] == 'captured', result
    return result


def restore_and_replay(setup, receipt, captured, index=0):
    from services.strategies import signal_input_capture as producer
    restored = core.restore_to_new(
        receipt.bundle.directory, setup['output'], restore_id='restore01',
        expected_manifest_sha256=receipt.bundle.manifest_sha256,
        limits=core.BundleLimits(500, 40_000_000, 5_000_000), deadline=time.monotonic() + 10,
    )
    account = setup['sources'][index].account
    name = account + '/data/' + captured['relativepath']
    directories = prefix.restored_recording_directories(
        restored.directory, account=account, journal_path=name,
        expected_manifest_sha256=restored.manifest_sha256,
        limits=core.BundleLimits(500, 40_000_000, 5_000_000), deadline=time.monotonic() + 10,
    )
    records = producer.read_runner_records(restored.directory / name)
    for record in records:
        directory = directories[record['payload']['object_scope']]
        assert producer.replay_runner_decision(record, object_directory=directory)['decision_match'] is True
    return restored, directories, records


def test_real_mixed_local_shared_archive_restores_and_replays(setup, monkeypatch, tmp_path):
    shared = tmp_path / 'shared'
    capture(setup, monkeypatch)
    captured = capture(setup, monkeypatch, shared=shared, loop=2)
    account = setup['sources'][0].account
    result = run(setup, shared_object_roots={account: shared})
    restored, directories, records = restore_and_replay(setup, result, captured)
    assert set(directories) == {'local', 'shared'}
    assert len(records) == 2
    assert result.bundle.offsite_verified is False
    cutoff = next(c for c in result.cutoffs if c.relative_path.endswith(captured['relativepath']))
    assert (restored.directory / cutoff.relative_path).stat().st_size == cutoff.size
    assert hashlib.sha256((restored.directory / cutoff.relative_path).read_bytes()).hexdigest() == cutoff.sha256


def test_shared_objects_deduplicated_across_two_accounts(setup, monkeypatch, tmp_path):
    shared = tmp_path / 'shared'
    capture(setup, monkeypatch, shared=shared)
    capture(setup, monkeypatch, index=1, shared=shared)
    roots = {a.account: shared for a in setup['sources'][:2]}
    result = run(setup, shared_object_roots=roots)
    copies = list(result.bundle.directory.rglob('shared_signal_inputs/*.json'))
    assert {p.name for p in copies} == {p.name for p in shared.glob('*.json')}
    assert len(copies) == len(list(shared.glob('*.json')))


def test_actual_writer_can_append_after_capture_without_changing_frozen_prefix(setup, monkeypatch):
    from services.strategies.signal_input_capture import _append_runner
    journal = next((setup['sources'][0].data_directory / 'runner_decisions').rglob('*.jsonl'))
    before = journal.read_bytes()
    original = core.create_bundle
    def append_after_copy(*args, **kwargs):
        result = original(*args, **kwargs)
        worker = threading.Thread(target=lambda: _append_runner(journal, json.loads(before)), daemon=True)
        worker.start()
        worker.join(timeout=3)
        assert not worker.is_alive()
        return result
    monkeypatch.setattr(core, 'create_bundle', append_after_copy)
    result = run(setup)
    name = setup['sources'][0].account + '/data/' + journal.relative_to(setup['sources'][0].data_directory).as_posix()
    assert journal.read_bytes() == before * 2
    assert (result.bundle.directory / name).read_bytes() == before


def test_references_published_after_initial_inventory_are_acquired(setup, monkeypatch, tmp_path):
    shared = tmp_path / 'shared'
    shared.mkdir()
    original = prefix._freeze_journal
    added = []
    # The pre-existing fixture journal is still the initial file set; place
    # the actual producer there so its new record is inside that cutoff.
    from services.strategies import signal_input_capture as producer
    from tests.test_runner_decision_capture import make_record
    root = setup['sources'][0].data_directory
    record = make_record()
    record['account_id'], record['session_id'] = '3' * 64, '4' * 32
    def publish_before_freeze(*args, **kwargs):
        if not added:
            monkeypatch.setenv('CBP_CAPTURE_RUNNER_DECISIONS', '1')
            monkeypatch.setenv('CBP_RUNNER_DECISION_OBJECT_DIR', str(shared))
            monkeypatch.setattr(producer, 'data_dir', lambda: root)
            monkeypatch.setattr(producer, '_runner_commit_identity', lambda: 'a' * 40)
            added.append(producer.capture_runner_decision(record))
        return original(*args, **kwargs)
    monkeypatch.setattr(prefix, '_freeze_journal', publish_before_freeze)
    result = run(setup, shared_object_roots={setup['sources'][0].account: shared})
    assert added[0]['status'] == 'captured'
    assert len(list(result.bundle.directory.rglob('shared_signal_inputs/*.json'))) == len(list(shared.glob('*.json')))


@pytest.mark.parametrize('change', ['truncate', 'rewrite', 'replace'])
def test_captured_prefix_changes_refuse_without_a_success_receipt(setup, monkeypatch, change):
    journal = next((setup['sources'][0].data_directory / 'runner_decisions').rglob('*.jsonl'))
    original = core.create_bundle
    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        raw = journal.read_bytes()
        if change == 'truncate':
            journal.write_bytes(raw[:5])
        elif change == 'rewrite':
            journal.write_bytes(raw.replace(b'local', b'other'))
        else:
            journal.unlink()
            journal.write_bytes(raw)
        return result
    monkeypatch.setattr(core, 'create_bundle', mutate)
    with pytest.raises(core.BundleError):
        run(setup)
    assert (setup['output'] / 'backup-batch0001' / core.MANIFEST).exists()


def test_incomplete_later_suffix_does_not_invalidate_complete_prefix(setup, monkeypatch):
    journal = next((setup['sources'][0].data_directory / 'runner_decisions').rglob('*.jsonl'))
    before = journal.read_bytes()
    original = core.create_bundle
    def append_partial(*args, **kwargs):
        result = original(*args, **kwargs)
        with journal.open('ab') as out:
            out.write(b'{"later_incomplete":')
        return result
    monkeypatch.setattr(core, 'create_bundle', append_partial)
    result = run(setup)
    cutoff = next(c for c in result.cutoffs if c.relative_path.startswith(setup['sources'][0].account + '/'))
    assert cutoff.size == len(before)


def test_busy_writer_refuses_immediately_and_initial_partial_tail_is_not_repaired(setup):
    journal = next((setup['sources'][0].data_directory / 'runner_decisions').rglob('*.jsonl'))
    with journal.open('rb') as held:
        fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(core.BundleError):
            run(setup)
    journal.write_bytes(journal.read_bytes()[:-1])
    raw = journal.read_bytes()
    with pytest.raises(core.BundleError):
        run(setup)
    assert journal.read_bytes() == raw
    assert list(setup['output'].iterdir()) == []


def test_shared_record_without_explicit_mapping_refuses(setup, monkeypatch, tmp_path):
    capture(setup, monkeypatch, shared=tmp_path / 'shared')
    with pytest.raises(core.BundleError):
        run(setup)
    assert list(setup['output'].iterdir()) == []


def test_unknown_artifact_is_refused_before_scratch_read(setup, monkeypatch):
    (setup['sources'][0].data_directory / 'config.json').write_bytes(b'{"api_token":"SYNTHETIC-private"}')
    called = []
    def trap(*args, **kwargs):
        called.append(True)
        raise AssertionError('must not open scratch')
    monkeypatch.setattr(prefix.tempfile, 'TemporaryFile', trap)
    with pytest.raises(core.BundleError):
        run(setup)
    assert called == []


def test_restored_mapping_requires_external_manifest_hash(setup, monkeypatch):
    captured = capture(setup, monkeypatch)
    result = run(setup)
    with pytest.raises(core.BundleError):
        prefix.restored_recording_directories(
            result.bundle.directory, account=setup['sources'][0].account,
            journal_path=setup['sources'][0].account + '/data/' + captured['relativepath'],
            expected_manifest_sha256='b' * 64, limits=core.BundleLimits(500, 40_000_000, 5_000_000),
            deadline=time.monotonic() + 10,
        )


def test_expired_or_tiny_budget_and_unsafe_shared_root_refuse(setup, tmp_path):
    with pytest.raises(core.BundleError):
        run(setup, deadline=time.monotonic() - 1)
    with pytest.raises(core.BundleError):
        run(setup, limits=core.BundleLimits(500, 100, 100))
    with pytest.raises(core.BundleError):
        run(setup, shared_object_roots={setup['sources'][0].account: setup['output']})
    assert list(setup['output'].iterdir()) == []


def test_new_session_after_inventory_is_explicitly_outside_capture(setup, monkeypatch):
    original = core.create_bundle
    root = setup['sources'][0].data_directory
    new_path = root / 'runner_decisions' / ('5' * 64) / ('6' * 32 + '.jsonl')
    raw = next((root / 'runner_decisions').rglob('*.jsonl')).read_bytes()
    def publish_new_session(*args, **kwargs):
        result = original(*args, **kwargs)
        new_path.parent.mkdir()
        new_path.write_bytes(raw)
        return result
    monkeypatch.setattr(core, 'create_bundle', publish_new_session)
    result = run(setup)
    name = setup['sources'][0].account + '/data/' + new_path.relative_to(root).as_posix()
    assert result.new_sessions == 'excluded_after_initial_inventory'
    assert name not in {c.relative_path for c in result.cutoffs}
    assert not (result.bundle.directory / name).exists()


@pytest.mark.parametrize('failure', ['missing', 'corrupt', 'hardlink', 'unknown_file'])
def test_missing_corrupt_linked_or_unrecognized_shared_object_refuses(setup, monkeypatch, tmp_path, failure):
    shared = tmp_path / 'shared'
    capture(setup, monkeypatch, shared=shared)
    path = next(p for p in shared.glob('*.json') if json.loads(p.read_bytes()).get('type') == 'completed_bar')
    if failure == 'missing':
        path.unlink()
    elif failure == 'corrupt':
        path.write_bytes(b'{}')
    elif failure == 'hardlink':
        (tmp_path / 'alias').hardlink_to(path)
    else:
        (shared / 'config.json').write_bytes(b'{"api_token":"SYNTHETIC-private"}')
    with pytest.raises(core.BundleError) as error:
        run(setup, shared_object_roots={setup['sources'][0].account: shared})
    assert 'SYNTHETIC-private' not in str(error.value)
    assert list(setup['output'].iterdir()) == []


def test_shared_publication_temporary_is_metadata_only(setup, monkeypatch, tmp_path):
    shared = tmp_path / 'shared'
    capture(setup, monkeypatch, shared=shared)
    temporary = shared / '.capture-a1b2c3d4'
    temporary.write_bytes(b'SYNTHETIC private unfinished content')
    result = run(setup, shared_object_roots={setup['sources'][0].account: shared})
    assert temporary.read_bytes() == b'SYNTHETIC private unfinished content'
    assert not list(result.bundle.directory.rglob('.capture-*'))


def test_initial_shared_cas_publication_two_link_window_safely_refuses(setup, monkeypatch, tmp_path):
    shared = tmp_path / 'shared'
    capture(setup, monkeypatch, shared=shared)
    (shared / '.capture-a1b2c3d4').hardlink_to(next(shared.glob('*.json')))
    with pytest.raises(core.BundleError):
        run(setup, shared_object_roots={setup['sources'][0].account: shared})
    assert list(setup['output'].iterdir()) == []


@pytest.mark.parametrize('change', ['destination', 'cross_account', 'wrong_size', 'duplicate_row'])
def test_hash_verified_but_malformed_restore_mapping_is_refused(setup, monkeypatch, change):
    captured = capture(setup, monkeypatch)
    account = setup['sources'][0].account
    original = core.create_bundle
    def corrupt_mapping(*args, **kwargs):
        artifacts = []
        for item in kwargs['artifacts']:
            if item.relative_path == account + '/data/' + prefix._NOTE:
                value = json.loads(item.stream.read(item.size))
                if change == 'destination':
                    value['object_directories']['local'] = '../../outside'
                elif change == 'cross_account':
                    value['journals'][0]['path'] = setup['sources'][1].account + '/data/runner_decisions/x/y.jsonl'
                elif change == 'wrong_size':
                    value['journals'][0]['bytes'] = True
                else:
                    value['journals'].append(value['journals'][0])
                raw = encoded(value)
                item = core.FileSource(item.relative_path, io.BytesIO(raw), len(raw), hashlib.sha256(raw).hexdigest())
            artifacts.append(item)
        kwargs['artifacts'] = artifacts
        return original(*args, **kwargs)
    monkeypatch.setattr(core, 'create_bundle', corrupt_mapping)
    result = run(setup)
    with pytest.raises(core.BundleError):
        prefix.restored_recording_directories(
            result.bundle.directory, account=account, journal_path=account + '/data/' + captured['relativepath'],
            expected_manifest_sha256=result.bundle.manifest_sha256,
            limits=core.BundleLimits(500, 40_000_000, 5_000_000), deadline=time.monotonic() + 10,
        )


def test_growing_journal_cannot_escape_file_byte_limit(setup, monkeypatch):
    original = prefix._freeze_journal
    changed = []
    def grow_before_freeze(path, *args, **kwargs):
        if not changed:
            changed.append(True)
            with path.open('ab') as out:
                out.write(path.read_bytes() * 100)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(prefix, '_freeze_journal', grow_before_freeze)
    with pytest.raises(core.BundleError, match='size_limit'):
        run(setup, limits=core.BundleLimits(500, 40_000_000, 16_384))
    assert list(setup['output'].iterdir()) == []


def test_final_prefix_verification_expiry_never_returns_success(setup, monkeypatch):
    now = [0.0]
    original = prefix._verify_prefix
    def expire(*args, **kwargs):
        original(*args, **kwargs)
        now[0] = 11.0
    monkeypatch.setattr(prefix, '_verify_prefix', expire)
    with pytest.raises(core.BundleError, match='deadline'):
        run(setup, deadline=10.0, clock=lambda: now[0])
