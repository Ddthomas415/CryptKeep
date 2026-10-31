"""Synthetic continuation records; no native calls, real token or operational approval."""
from dataclasses import replace
import fcntl
import hashlib
import json
import os
from pathlib import Path

import pytest

from scripts.research import companion_cutover as entry
from scripts.research import companion_cutover_continuation as continuation
from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from tests.test_companion_cutover_entrypoint import (
    setup, invoke, assert_no_dispatch, assert_restored,
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_review(state, record):
    raw = install.canonical(record)
    state.review_path.write_bytes(raw)
    index = state.args.index('--reviewed-continuation-review-sha256')
    state.args[index + 1] = digest(raw)


@pytest.fixture
def resumed(setup):
    state = setup
    state.directory.mkdir(parents=True, mode=0o700)
    hashes = {'manifest_sha256': state.plan.manifest_sha256,
              'preparation_evidence_sha256': state.prepared.evidence_sha256,
              'preparation_review_sha256': 'a' * 64, 'runtime_review_sha256': 'a' * 64}
    state.prior_rows = [
        {'phase': 'cutover_inputs_bound', 'installation_evidence': hashes},
        {'phase': 'installation_reserved', 'installation_evidence': {
            'startup_authorized': True, 'deferred_startup_policies': list(state.plan.deferred_startup_policies),
            'network_contract': network.CONTRACT, 'network_connectivity_verified': False}},
        {'phase': 'runtime_operation_intended', 'installation_evidence': {'operation': 'staged_checks'}},
        {'phase': 'installation_failed', 'installation_evidence': {'stage': 'staged_preflight'}},
    ]
    state.prior = state.directory / 'receipt.jsonl'
    state.prior.touch(mode=0o600)
    state.prior.write_bytes(b''.join(install.canonical(row) + b'\n' for row in state.prior_rows))
    state.prior_bytes = state.prior.read_bytes()
    consumers = {}
    for name in continuation.CONSUMERS:
        path = state.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(('SYNTHETIC source bytes: ' + name).encode())
        consumers[name] = digest(path.read_bytes())
    state.record = {'schema': 'companion-prestart-continuation-v1',
                    'decision': 'ACCEPTED_WITH_RISK', 'reviewer': 'SYNTHETIC fixture, not independent acceptance',
                    'execution_id': 'continuationfixture01', **hashes,
                    'prepared_ids': [row.id for row in state.prepared.replacements],
                    'prior_receipt_sha256': digest(state.prior_bytes), 'consumer_sha256': consumers}
    state.review_path = state.root.parent / 'continuation-review.json'
    state.args.extend(('--continuation-review', str(state.review_path),
                       '--reviewed-continuation-review-sha256', '0' * 64))
    write_review(state, state.record)
    state.new_directory = state.directory.parent / state.record['execution_id']
    return state


def test_continuation_default_validates_without_reserving_or_dispatching(resumed, capsys):
    code, result = invoke(resumed, capsys, execute=False)
    assert code == 0 and result['actions_executed'] is False
    assert result['continuation']['execution_id'] == resumed.record['execution_id']
    assert result['continuation']['preparation_attempt'] == resumed.plan.attempt
    assert not resumed.new_directory.exists() and not resumed.lock.exists()
    assert resumed.prior.read_bytes() == resumed.prior_bytes
    assert_no_dispatch(resumed)


def test_continuation_executes_same_plan_and_ids_once_in_separate_receipt(resumed, capsys):
    code, result = invoke(resumed, capsys)
    assert code == 0 and result['query_passed'] is True
    assert result['receipt'] == str(resumed.new_directory / 'receipt.jsonl')
    assert resumed.prior.read_bytes() == resumed.prior_bytes
    assert {resumed.backend.rows[n].id for n in install.APPS} == set(resumed.record['prepared_ids'])
    methods = [name for name, _ in resumed.backend.calls]
    assert not {'build', 'create', 'create_staged'}.intersection(methods)
    assert methods.count('runtime_explain') == 1 and methods.count('runtime_start') == 4
    assert resumed.runners[0].plan == resumed.plan
    first = json.loads((resumed.new_directory / 'receipt.jsonl').read_text().splitlines()[0])
    assert first['installation_evidence']['preparation_attempt'] == resumed.plan.attempt
    assert first['installation_evidence']['execution_id'] == resumed.record['execution_id']
    count = len(resumed.backend.calls)
    tokens = sum(event[0] == 'token' for event in resumed.events)
    code, result = invoke(resumed, capsys)
    assert code == 1 and result['failure_phase'] == 'reservation'
    assert len(resumed.backend.calls) == count
    assert sum(event[0] == 'token' for event in resumed.events) == tokens


@pytest.mark.parametrize('key,value', [
    ('decision', 'READY_FOR_INDEPENDENT_REVIEW'), ('reviewer', ''), ('execution_id', '../outside'),
    ('execution_id', 'short'), ('manifest_sha256', 'f' * 64),
    ('preparation_evidence_sha256', 'f' * 64), ('preparation_review_sha256', 'f' * 64),
    ('runtime_review_sha256', 'f' * 64), ('prepared_ids', ['f' * 64] * 4),
    ('prior_receipt_sha256', 'f' * 64), ('consumer_sha256', {}),
])
def test_invalid_review_bindings_refuse_before_lock_or_token(resumed, capsys, key, value):
    write_review(resumed, {**resumed.record, key: value})
    assert invoke(resumed, capsys)[0] == 1
    assert not resumed.lock.exists() and not resumed.new_directory.exists()
    assert_no_dispatch(resumed)


@pytest.mark.parametrize('change', ['wrong_hash', 'same_id', 'changed_source', 'extra_field', 'duplicate'])
def test_review_cannot_override_trust_source_or_schema(resumed, capsys, change):
    if change == 'wrong_hash':
        resumed.review_path.write_bytes(b'{}')
    elif change == 'changed_source':
        (resumed.root / continuation.CONSUMERS[0]).write_bytes(b'changed')
    elif change == 'duplicate':
        raw = resumed.review_path.read_bytes()[:-1] + b',"decision":"ACCEPTED_WITH_RISK"}'
        resumed.review_path.write_bytes(raw)
        resumed.args[-1] = digest(raw)
    else:
        record = dict(resumed.record)
        record.update(execution_id=resumed.plan.attempt) if change == 'same_id' else record.update(extra=True)
        write_review(resumed, record)
    assert invoke(resumed, capsys)[0] == 1
    assert_no_dispatch(resumed)


@pytest.mark.parametrize('missing', ['--continuation-review', '--reviewed-continuation-review-sha256'])
def test_continuation_options_must_be_supplied_together(resumed, capsys, missing):
    i = resumed.args.index(missing)
    del resumed.args[i:i + 2]
    assert invoke(resumed, capsys)[0] == 1
    assert_no_dispatch(resumed)


@pytest.mark.parametrize('change', ['started', 'extra', 'truncated', 'binding', 'numeric_bool'])
def test_only_exact_bound_prestart_failure_is_eligible(resumed, capsys, change):
    rows = json.loads(json.dumps(resumed.prior_rows))
    if change == 'started':
        rows[2]['installation_evidence']['operation'] = 'start'
    elif change == 'extra':
        rows.append({'phase': 'quiesce_intended'})
    elif change == 'truncated':
        rows.pop()
    elif change == 'numeric_bool':
        rows[1]['installation_evidence']['startup_authorized'] = 1
    else:
        rows[0]['installation_evidence']['runtime_review_sha256'] = 'f' * 64
    raw = b''.join(install.canonical(row) + b'\n' for row in rows)
    resumed.prior.write_bytes(raw)
    write_review(resumed, {**resumed.record, 'prior_receipt_sha256': digest(raw)})
    assert invoke(resumed, capsys)[0] == 1
    assert_no_dispatch(resumed)


@pytest.mark.parametrize('target', ['review', 'prior'])
def test_binding_rechecked_under_lock_before_new_reservation_or_token(resumed, capsys, monkeypatch, target):
    flock = entry.fcntl.flock
    def change(fd, flags):
        flock(fd, flags)
        (resumed.review_path if target == 'review' else resumed.prior).write_bytes(b'changed')
    monkeypatch.setattr(entry.fcntl, 'flock', change)
    code, result = invoke(resumed, capsys)
    assert code == 1 and result['failure_phase'] == 'continuation_recheck'
    assert not resumed.new_directory.exists()
    assert_no_dispatch(resumed)


@pytest.mark.parametrize('target', ['prior_file', 'prior_directory', 'new_directory'])
def test_symlinks_are_not_followed(resumed, capsys, target):
    outside = resumed.root.parent / 'outside'
    if target == 'prior_file':
        outside.write_bytes(resumed.prior_bytes)
        resumed.prior.unlink()
        resumed.prior.symlink_to(outside)
    elif target == 'prior_directory':
        resumed.directory.rename(outside)
        resumed.directory.symlink_to(outside, target_is_directory=True)
    else:
        outside.mkdir(mode=0o700)
        resumed.new_directory.symlink_to(outside, target_is_directory=True)
    assert invoke(resumed, capsys)[0] == 1
    assert_no_dispatch(resumed)


def test_busy_shared_lock_does_not_reserve_or_consume_token(resumed, capsys):
    fd = os.open(resumed.lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert invoke(resumed, capsys)[0] == 1
        assert not resumed.new_directory.exists()
        assert_no_dispatch(resumed)
    finally:
        os.close(fd)


@pytest.mark.parametrize('change', ['original', 'replacement'])
def test_continuation_still_checks_fresh_native_fixture_state(resumed, capsys, change):
    name = install.APPS[0] if change == 'original' else resumed.prepared.replacements[0].name
    resumed.backend.rows[name] = replace(resumed.backend.rows[name], metadata='0' * 64)
    code, result = invoke(resumed, capsys)
    assert code == 1 and result['services_started'] is False and result['query_attempted'] is False
    assert resumed.prior.read_bytes() == resumed.prior_bytes
    assert not any(method in {'runtime_start', 'quiesce', 'rename'} for method, _ in resumed.backend.calls)


def test_continuation_retains_owned_rollback_and_prior_receipt(resumed, capsys, monkeypatch):
    monkeypatch.setattr(entry, '_publish', lambda *args: False)
    code, result = invoke(resumed, capsys)
    assert code == 1 and result['rollback_verified'] is True
    assert len(resumed.rollbacks) == 1
    assert resumed.prior.read_bytes() == resumed.prior_bytes
    assert (resumed.new_directory / 'receipt.jsonl').is_file()
    assert_restored(resumed)


@pytest.mark.parametrize('mode', [0o644, 0o660])
def test_prior_receipt_must_remain_private(resumed, capsys, mode):
    resumed.prior.chmod(mode)
    assert invoke(resumed, capsys)[0] == 1
    assert_no_dispatch(resumed)


def test_failed_reservation_fsync_remains_consumed_without_dispatch(resumed, capsys, monkeypatch):
    sync = entry.os.fsync
    monkeypatch.setattr(entry.os, 'fsync', lambda fd: (_ for _ in ()).throw(OSError('SYNTHETIC_SECRET')))
    code, result = invoke(resumed, capsys)
    assert code == 1 and result['failure_phase'] == 'reservation'
    assert resumed.new_directory.is_dir() and list(resumed.new_directory.iterdir()) == []
    assert resumed.prior.read_bytes() == resumed.prior_bytes
    assert_no_dispatch(resumed)
    monkeypatch.setattr(entry.os, 'fsync', sync)
    assert invoke(resumed, capsys)[0] == 1
    assert_no_dispatch(resumed)
