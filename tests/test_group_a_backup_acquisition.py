"""Synthetic declared-root acquisition; no operating data or provider access."""
from contextlib import ExitStack
import hashlib
import json
import sqlite3
import time

import pytest

from services.control import group_a_backup_acquisition as acquire
from services.control import group_a_backup_bundle as bundle


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


@pytest.fixture
def setup(tmp_path):
    with ExitStack() as stack:
        sources = []
        configs = {}
        for account in sorted(bundle._accounts('fixture1')):
            root = tmp_path / account / 'data'
            root.mkdir(parents=True)
            stores = []
            for name in ('paper_trading.sqlite', 'intent_queue.sqlite', 'strategy_state.sqlite'):
                path = root / name
                writer = sqlite3.connect(path)
                stack.callback(writer.close)
                writer.execute('PRAGMA journal_mode=WAL')
                writer.execute('CREATE TABLE evidence(value INTEGER)')
                writer.execute('INSERT INTO evidence VALUES(100001)')
                writer.commit()
                reader = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
                stack.callback(reader.close)
                reader.execute('PRAGMA query_only=ON')
                stores.append(bundle.SQLiteSource(account + '/data/' + name, reader))
            objects = root / 'signal_inputs'
            objects.mkdir()
            def store(value):
                raw = encoded(value)
                digest = hashlib.sha256(raw).hexdigest()
                (objects / (digest + '.json')).write_bytes(raw)
                return digest
            bar = store({'version': 2, 'type': 'completed_bar', 'row': [1, 2, 3, 4, 5, 6]})
            payload = {
                'object_scope': 'local',
                'settings_sha256': store({'version': 2, 'type': 'runner_settings'}),
                'code_sha256': store({'version': 2, 'type': 'runner_code'}),
                'completed_prefix_sha256': store({'version': 2, 'type': 'completed_prefix', 'bar_refs': [bar]}),
            }
            decisions = root / 'runner_decisions' / ('3' * 64)
            decisions.mkdir(parents=True)
            (decisions / ('4' * 32 + '.jsonl')).write_bytes(encoded({
                'sha256': hashlib.sha256(encoded(payload)).hexdigest(), 'payload': payload,
            }) + b'\n')
            sources.append(acquire.AccountSource(account, root, tuple(stores)))
            configs[account] = {'execution': {'live_enabled': False}}
        output = tmp_path / 'backups'
        output.mkdir(mode=0o700)
        yield dict(sources=sources, configs=configs, output=output)


def run(setup, **kwargs):
    return acquire.acquire_bundle(
        setup['output'], release='fixture1', bundle_id='batch0001',
        accounts=setup['sources'], public_configurations=setup['configs'],
        public_run_manifest={'release': 'fixture1', 'source_sha256': 'a' * 64},
        limits=kwargs.pop('limits', bundle.BundleLimits(200, 20_000_000, 1_000_000)),
        deadline=kwargs.pop('deadline', time.monotonic() + 20), **kwargs,
    )


def test_nine_roots_real_wal_and_recording_objects_round_trip(setup):
    result = run(setup)
    assert result.account_count == 9
    assert result.sources_revalidated is True
    assert result.bundle.offsite_verified is False
    restored = bundle.restore_to_new(
        result.bundle.directory, setup['output'], restore_id='restore01',
        expected_manifest_sha256=result.bundle.manifest_sha256,
        limits=bundle.BundleLimits(200, 20_000_000, 1_000_000), deadline=time.monotonic() + 10,
    )
    for account in setup['sources']:
        for path in account.data_directory.rglob('*'):
            if path.is_file() and not path.name.endswith(('-wal', '-shm')):
                copy = restored.directory / account.account / 'data' / path.relative_to(account.data_directory)
                if path.suffix != '.sqlite':
                    assert copy.read_bytes() == path.read_bytes()
                else:
                    with sqlite3.connect(copy) as con:
                        assert con.execute('SELECT value FROM evidence').fetchone() == (100001,)
        assert all(db.source.execute('PRAGMA query_only').fetchone() == (1,) for db in account.databases)


@pytest.mark.parametrize('failure', ['missing_account', 'missing_config', 'missing_db', 'unmapped_db',
    'wrong_connection', 'same_root', 'link', 'hardlink', 'unknown_file', 'orphan_sidecar',
    'missing_object', 'shared_objects', 'partial_record', 'changed_object'])
def test_incomplete_or_unsafe_sources_refused_before_output(setup, failure):
    source = setup['sources'][0]
    root = source.data_directory
    if failure == 'missing_account':
        setup['sources'].pop()
    elif failure == 'missing_config':
        setup['configs'].pop(source.account)
    elif failure == 'missing_db':
        # Keep the live connection intact: refuse its missing named source.
        (root / 'paper_trading.sqlite').rename(root / 'moved.sqlite')
    elif failure == 'unmapped_db':
        (root / 'extra.sqlite').write_bytes(b'not an attributed database')
    elif failure == 'wrong_connection':
        other = setup['sources'][1]
        stores = (bundle.SQLiteSource(source.databases[0].relative_path, other.databases[0].source), *source.databases[1:])
        setup['sources'][0] = acquire.AccountSource(source.account, root, stores)
    elif failure == 'same_root':
        other = setup['sources'][1]
        setup['sources'][1] = acquire.AccountSource(other.account, root, other.databases)
    elif failure == 'link':
        (root / 'link.json').symlink_to(root / 'paper_trading.sqlite')
    elif failure == 'hardlink':
        (root / 'alias.json').hardlink_to(next((root / 'signal_inputs').iterdir()))
    elif failure == 'unknown_file':
        (root / 'private.yaml').write_bytes(b'SYNTHETIC-private')
    elif failure == 'orphan_sidecar':
        (root / 'unmapped.sqlite-wal').write_bytes(b'SYNTHETIC-private')
    elif failure == 'missing_object':
        next((root / 'signal_inputs').iterdir()).unlink()
    elif failure in ('shared_objects', 'partial_record'):
        path = next((root / 'runner_decisions').rglob('*.jsonl'))
        if failure == 'partial_record':
            path.write_bytes(path.read_bytes()[:-1])
        else:
            obj = json.loads(path.read_bytes())
            obj['payload']['object_scope'] = 'shared'
            obj['sha256'] = hashlib.sha256(encoded(obj['payload'])).hexdigest()
            path.write_bytes(encoded(obj) + b'\n')
    elif failure == 'changed_object':
        next((root / 'signal_inputs').iterdir()).write_bytes(b'{}')
    with pytest.raises(bundle.BundleError) as error:
        run(setup)
    assert 'SYNTHETIC-private' not in str(error.value)
    assert list(setup['output'].iterdir()) == []


@pytest.mark.parametrize('change', ['append', 'rewrite_same_size', 'add', 'remove', 'replace'])
def test_changes_after_copy_never_return_acquisition_success(setup, monkeypatch, change):
    original = bundle.create_bundle
    root = setup['sources'][0].data_directory
    path = next((root / 'runner_decisions').rglob('*.jsonl'))
    def change_after_copy(*args, **kwargs):
        receipt = original(*args, **kwargs)
        raw = path.read_bytes()
        if change == 'append':
            path.write_bytes(raw + b'\n')
        elif change == 'rewrite_same_size':
            path.write_bytes(raw.replace(b'local', b'other'))
        elif change == 'add':
            (root / 'added.json').write_bytes(b'{}')
        elif change == 'remove':
            path.unlink()
        else:
            path.rename(path.with_suffix('.old'))
            path.write_bytes(raw)
        return receipt
    monkeypatch.setattr(bundle, 'create_bundle', change_after_copy)
    with pytest.raises(bundle.BundleError):
        run(setup)
    assert (setup['output'] / 'backup-batch0001' / bundle.MANIFEST).exists()


def test_output_inside_any_source_root_is_refused(setup):
    setup['output'] = setup['sources'][0].data_directory / 'output'
    setup['output'].mkdir(mode=0o700)
    with pytest.raises(bundle.BundleError):
        run(setup)
    assert list(setup['output'].iterdir()) == []


def test_expired_or_small_budget_refuses_without_output(setup):
    with pytest.raises(bundle.BundleError):
        run(setup, deadline=time.monotonic() - 1)
    with pytest.raises(bundle.BundleError):
        run(setup, limits=bundle.BundleLimits(200, 100, 100))
    assert list(setup['output'].iterdir()) == []


def test_actual_existing_capture_producer_survives_acquisition_and_restore(setup, monkeypatch):
    from services.strategies import signal_input_capture as capture
    from tests.test_runner_decision_capture import make_record

    root = setup['sources'][0].data_directory
    monkeypatch.setenv('CBP_CAPTURE_RUNNER_DECISIONS', '1')
    monkeypatch.delenv('CBP_RUNNER_DECISION_OBJECT_DIR', raising=False)
    monkeypatch.setattr(capture, 'data_dir', lambda: root)
    monkeypatch.setattr(capture, '_runner_commit_identity', lambda: 'a' * 40)
    before = capture.capture_runner_decision(make_record())
    assert before['status'] == 'captured', before
    result = run(setup)
    restored = bundle.restore_to_new(
        result.bundle.directory, setup['output'], restore_id='producer1',
        expected_manifest_sha256=result.bundle.manifest_sha256,
        limits=bundle.BundleLimits(200, 20_000_000, 1_000_000), deadline=time.monotonic() + 10,
    )
    copied = restored.directory / setup['sources'][0].account / 'data'
    envelopes = capture.read_runner_records(copied / before['relativepath'])
    assert capture.replay_runner_decision(envelopes[0], object_directory=copied / 'signal_inputs')['decision_match'] is True


def test_final_hashing_deadline_expiry_cannot_return_acquisition_receipt(setup, monkeypatch):
    now = [0.0]
    original = acquire._read_source
    original_create = bundle.create_bundle
    copied = [False]
    def note_copy(*args, **kwargs):
        result = original_create(*args, **kwargs)
        copied[0] = True
        return result
    def expire(*args, **kwargs):
        result = original(*args, **kwargs)
        if copied[0]:
            now[0] = 11.0
        return result
    monkeypatch.setattr(bundle, 'create_bundle', note_copy)
    monkeypatch.setattr(acquire, '_read_source', expire)
    with pytest.raises(bundle.BundleError, match='deadline'):
        run(setup, deadline=10.0, clock=lambda: now[0])


def test_scratch_write_failure_preserves_caller_connections_and_hides_details(setup, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError('SYNTHETIC-private disk failure')
    monkeypatch.setattr(acquire.tempfile, 'TemporaryFile', fail)
    with pytest.raises(bundle.BundleError) as error:
        run(setup)
    assert 'SYNTHETIC-private' not in str(error.value)
    assert list(setup['output'].iterdir()) == []
    assert all(db.source.execute('SELECT 1').fetchone() == (1,)
               for account in setup['sources'] for db in account.databases)


def test_new_file_during_final_rehash_refuses(setup, monkeypatch):
    original = acquire._read_source
    original_create = bundle.create_bundle
    copied = [False]
    def note_copy(*args, **kwargs):
        result = original_create(*args, **kwargs)
        copied[0] = True
        return result
    def add_file(*args, **kwargs):
        result = original(*args, **kwargs)
        if copied[0]:
            (setup['sources'][0].data_directory / 'late.json').write_bytes(b'{}')
        return result
    monkeypatch.setattr(bundle, 'create_bundle', note_copy)
    monkeypatch.setattr(acquire, '_read_source', add_file)
    with pytest.raises(bundle.BundleError):
        run(setup)


def test_final_revalidation_rehashes_even_when_metadata_appears_unchanged(setup, monkeypatch):
    signature = acquire._signature
    def metadata_without_timestamps(info, kind):
        value = signature(info, kind)
        return value[:-2] if kind == 'artifact' else value
    monkeypatch.setattr(acquire, '_signature', metadata_without_timestamps)
    original = bundle.create_bundle
    path = next((setup['sources'][0].data_directory / 'runner_decisions').rglob('*.jsonl'))
    def change_bytes(*args, **kwargs):
        result = original(*args, **kwargs)
        path.write_bytes(path.read_bytes().replace(b'local', b'other'))
        return result
    monkeypatch.setattr(bundle, 'create_bundle', change_bytes)
    with pytest.raises(bundle.BundleError, match='source_bytes_changed_after_copy'):
        run(setup)


def test_deadline_consumed_by_final_receipt_hash_cannot_return_success(setup, monkeypatch):
    now = [0.0]
    original = bundle._encode
    def expire_after_encode(value):
        raw = original(value)
        if value and all('/data/' in key for key in value):
            now[0] = 11.0
        return raw
    monkeypatch.setattr(bundle, '_encode', expire_after_encode)
    with pytest.raises(bundle.BundleError, match='deadline'):
        run(setup, deadline=10.0, clock=lambda: now[0])


@pytest.mark.parametrize('name', ['config.json', 'api_keys.json', 'public_notes.json', 'exports.csv'])
def test_unknown_producer_path_is_refused_before_payload_or_scratch_read(setup, monkeypatch, name):
    (setup['sources'][0].data_directory / name).write_bytes(b'{"api_token":"SYNTHETIC-private"}')
    called = []
    def trap(*args, **kwargs):
        called.append(True)
        raise AssertionError('must refuse before reading payload or opening scratch')
    monkeypatch.setattr(acquire, '_read_source', trap)
    monkeypatch.setattr(acquire.tempfile, 'TemporaryFile', trap)
    with pytest.raises(bundle.BundleError, match='unrecognized_artifact_path'):
        run(setup)
    assert called == []
    assert list(setup['output'].iterdir()) == []
