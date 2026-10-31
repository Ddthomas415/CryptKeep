"""Offline saved-row replay and fixed-schema lifecycle diagnostics; no live operations."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import socket
import subprocess

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_install_docker as docker
from scripts.research import companion_installer as install
from tests.test_companion_running_backend import backend
from tests.test_companion_staged_update import harness, reviewed, StagedRuntime


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Quiesce diagnostics test attempted real native/network work')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)


@pytest.mark.parametrize('case,stage,attempted,ack,confirmed', [
    ('target', 'target_validation', False, False, False),
    ('pre_observation', 'pre_observation', False, False, False),
    ('pre_state', 'pre_state', False, False, False),
    ('command_before', 'signal_command', True, False, False),
    ('command_after', 'signal_command', True, False, False),
    ('post_observation', 'post_observation', True, True, False),
    ('timeout', 'exit_timeout', True, True, False),
    ('success', 'exit_verified', True, True, True),
])
def test_fixed_report_distinguishes_refusals_without_changing_commands(
        backend, monkeypatch, case, stage, attempted, ack, confirmed):
    native, commands, clock = backend
    before = native.plan.baseline[-1]
    identity = before.id
    if case == 'target':
        identity = native.plan.baseline[0].id
    elif case == 'pre_observation':
        commands.rows[before.id]['image'] = 'sha256:' + 'f' * 64
    elif case == 'pre_state':
        monkeypatch.setattr(native, '_observe_original', lambda *a, **k: replace(before, state='exited'))
    elif case in {'command_before', 'command_after'}:
        commands.ack = case.removeprefix('command_')
    elif case == 'post_observation':
        commands.after_mutation = lambda: commands.rows[before.id].update(image='sha256:' + 'f' * 64)
    elif case == 'timeout':
        commands.responsive = False
    report = native.quiesce_report(identity)
    assert install.validate_quiesce_report(report) == {
        'schema': 'companion-quiesce-report-v1', 'stage': stage,
        'command_attempted': attempted, 'command_acknowledged': ack, 'confirmed': confirmed}
    assert commands.mutations() == ([('container', 'kill', '--signal=SIGTERM', before.id)] if attempted else [])
    assert clock.now <= docker.LIFECYCLE_TIMEOUT + 0.01
    assert 'SYNTHETIC_PRIVATE_ERROR' not in json.dumps(report)
    assert not any('SIGKILL' in str(call) or '--force' in str(call) for call in commands.calls)
    if case == 'command_after':
        assert commands.rows[before.id]['state'] == 'exited'
        assert report['confirmed'] is False


def test_report_crosses_real_child_json_boundary_without_exception_payload(backend):
    native, commands, _ = backend
    commands.ack = 'after'
    report = core.ProcessExecutor().call(native.quiesce_report, (native.plan.baseline[-1].id,), 3)
    assert install.validate_quiesce_report(report)['stage'] == 'signal_command'
    assert report['confirmed'] is False and report['command_acknowledged'] is False
    assert 'SYNTHETIC_PRIVATE_ERROR' not in json.dumps(report)


@pytest.mark.parametrize('change', ['unknown_stage', 'extra_payload', 'numeric_bool', 'false_confirmation', 'ack_without_attempt'])
def test_malformed_report_is_not_an_acceptance_or_logging_channel(change):
    report = {'schema': 'companion-quiesce-report-v1', 'stage': 'signal_command',
              'command_attempted': True, 'command_acknowledged': False, 'confirmed': False}
    if change == 'unknown_stage': report['stage'] = 'SYNTHETIC_PRIVATE_ERROR'
    elif change == 'extra_payload': report['error'] = 'SYNTHETIC_PRIVATE_ERROR'
    elif change == 'numeric_bool': report['command_attempted'] = 1
    elif change == 'false_confirmation': report['confirmed'] = True
    else: report.update(command_attempted=False, command_acknowledged=True)
    with pytest.raises(core.Refused):
        install.validate_quiesce_report(report)


def run_with_report(case, receipt_failure=False):
    plan, backend, _, prepare = harness()
    prepared_result = prepare.prepare_staged(plan, authorized=True)
    prepared = reviewed(plan, prepared_result['preparation_evidence'])
    backend.calls.clear()
    receipt = type(prepare.receipt)()
    if receipt_failure:
        write = receipt.write
        def fail(event):
            if event['phase'] == 'quiesce_diagnostic':
                raise RuntimeError('SYNTHETIC_PRIVATE_ERROR')
            write(event)
        receipt.write = fail
    runner = install.Installer(backend, receipt, executor=prepare.executor)
    runtime = StagedRuntime(backend)
    calls = []
    def report(identity):
        calls.append(identity)
        confirmed = case in {'success', 'fresh_drift'}
        if confirmed:
            assert backend.quiesce(identity) is True
        if case == 'fresh_drift':
            name = next(r.name for r in plan.baseline if r.id == identity)
            backend.rows[name] = replace(backend.rows[name], image='sha256:' + 'f' * 64)
        result = {'schema': 'companion-quiesce-report-v1',
                  'stage': 'exit_verified' if confirmed else 'signal_command',
                  'command_attempted': True, 'command_acknowledged': confirmed, 'confirmed': confirmed}
        if case == 'malformed': result['payload'] = 'SYNTHETIC_PRIVATE_ERROR'
        return result
    backend.quiesce_report = report
    result = runner.run(plan, authorized=True, runtime=runtime, startup_authorized=True, prepared=prepared)
    return plan, backend, receipt, runner, calls, result


def test_parent_records_confirmed_diagnostic_but_still_uses_existing_guards():
    plan, backend, receipt, _, calls, result = run_with_report('success')
    assert result['query_passed'] is True
    assert calls == [r.id for r in reversed(plan.baseline[3:])]
    reports = [r for r in receipt.events if r['phase'] == 'quiesce_diagnostic']
    assert len(reports) == 4 and all(r['installation_evidence']['confirmed'] for r in reports)
    assert sum(m == 'runtime_explain' for m, _ in backend.calls) == 1


@pytest.mark.parametrize('case', ['refused', 'malformed', 'fresh_drift'])
def test_parent_never_promotes_report_without_confirmed_fresh_state(case):
    plan, backend, receipt, _, calls, result = run_with_report(case)
    assert result['running_update_complete'] is False and result['query_attempted'] is False
    assert result['unresolved_quiesce'] == [plan.baseline[-1].name]
    assert len(calls) == 1 and not any(m == 'restart_original' for m, _ in backend.calls)
    assert not any(r['phase'] == 'quiesce_confirmed' for r in receipt.events)
    assert 'SYNTHETIC_PRIVATE_ERROR' not in json.dumps(receipt.events)
    assert sum(r['phase'] == 'quiesce_diagnostic' for r in receipt.events) == (0 if case == 'malformed' else 1)


def test_diagnostic_receipt_failure_does_not_lose_verified_owned_shutdown():
    plan, backend, receipt, _, calls, result = run_with_report('success', receipt_failure=True)
    assert result['query_attempted'] is False and result['receipt_complete'] is False
    assert result['unresolved_quiesce'] == []
    assert calls == [plan.baseline[-1].id]
    assert sum(method == 'restart_original' for method, _ in backend.calls) == 1
    assert all(backend.rows[row.name].state == 'running' for row in plan.baseline)
    assert 'SYNTHETIC_PRIVATE_ERROR' not in json.dumps(receipt.events)


@pytest.mark.parametrize('with_stages', [False, True])
def test_saved_precleanup_state_replay(with_stages):
    root = Path(__file__).resolve().parents[1]
    base = root / 'docs/review_artifacts/companion_continuation_20261021'
    manifest = (base / 's3_source_refresh_plan/reviewed_preparation_manifest.json').read_bytes()
    plan = install.Plan.load(manifest, 'dd7b537aa39d2f5cbccebf41a20fadc7e2ae8e22ebe20063daf7417286dddb6d')
    prior = (base / 'runtime_packet/post_attempt_inventory.json').read_bytes()
    staged = (base / 'runtime_packet/staged_metadata.derived.json').read_bytes()
    assert hashlib.sha256(prior).hexdigest() == '2fa8fec71dc7879db92a9adb414765d0caafadce171c6013408882b041667c1b'
    assert hashlib.sha256(staged).hexdigest() == '98c186a31d78686bf7702eb46685c87a2d6487a680cad0e702a35244c7eed118'
    saved = json.loads(prior)['rows']
    stages = json.loads(staged)['rows']
    rows = {r['id']: deepcopy(r) for r in saved[:-4]}
    if with_stages: rows.update({r['id']: deepcopy(r) for r in stages})
    calls = []
    def command(args, **kwargs):
        calls.append(args[:2])
        if args[:2] == ('container', 'ls'):
            return '\n'.join(r['id'] + ' ' + r['name'].removeprefix('/') for r in rows.values()).encode()
        if args[:2] == ('network', 'inspect'):
            return b'\n'.join(json.dumps({'id': v, 'name': k}).encode() for k, v in plan.network_bindings)
        if args[:2] == ('container', 'inspect'):
            return b'\n'.join(json.dumps(rows[i]).encode() for i in args[4:])
        raise AssertionError('Saved replay attempted non-inspection work')
    native = docker.DockerInstallBackend(plan, root)
    native._command = command
    default = native.inventory()
    explicit = native.inventory(tuple(r['id'] for r in stages) if with_stages else ())
    assert default == explicit and len(default) == (11 if with_stages else 7)
    assert native._observe_original(plan.baseline[-1], 10**20) == plan.baseline[-1]
    assert all(c in {('container', 'ls'), ('container', 'inspect'), ('network', 'inspect')} for c in calls)
