"""Offline running-storage installation component; no runtime authorization."""
from dataclasses import replace
import hashlib
import json

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from tests.test_companion_installer import ConfiguredBackend, Inline, Receipt, configured_manifest, load


def running_manifest():
    data = configured_manifest()
    data['schema'] = 'companion-running-storage-install-v4'
    for row in data['baseline']:
        row['state'] = 'running'
    return data


class RunningBackend(ConfiguredBackend):
    def quiesce(self, cid):
        def change():
            key, row = next((n, r) for n, r in self.rows.items() if r.id == cid)
            assert key in install.APPS and row.state == 'running'
            self.rows[key] = replace(row, state='exited')
            return True
        return self.effect('quiesce', change, cid)

    def restart_original(self, cid):
        def change():
            key, row = next((n, r) for n, r in self.rows.items() if r.id == cid)
            assert key in install.APPS and row.state == 'exited'
            self.rows[key] = replace(row, state='running', started='new-start')
            return True
        return self.effect('restart_original', change, cid)


def setup_runner(**kwargs):
    plan = load(running_manifest())
    backend, receipt = RunningBackend(plan, **kwargs), Receipt()
    runner = install.Installer(backend, receipt, executor=Inline())
    return plan, backend, receipt, runner


@pytest.mark.parametrize('index', range(7))
def test_v4_requires_all_originals_running(index):
    data = running_manifest()
    data['baseline'][index]['state'] = 'exited'
    with pytest.raises(core.Refused):
        load(data)


@pytest.mark.parametrize('index', range(7))
def test_old_configured_profile_still_refuses_running_original(index):
    data = configured_manifest()
    data['baseline'][index]['state'] = 'running'
    with pytest.raises(core.Refused):
        load(data)


@pytest.mark.parametrize('change', ['network_contract', 'extra', 'startup'])
def test_v4_does_not_relax_existing_contract(change):
    data = running_manifest()
    if change == 'network_contract':
        del data['network_contract']
    elif change == 'extra':
        data['implicitly_authorized'] = True
    else:
        data['policies']['sdk_startup_compatible'] = True
    with pytest.raises(core.Refused):
        load(data)


def test_all_images_prepared_before_any_quiesce_and_storage_untouched():
    plan, backend, receipt, runner = setup_runner()
    result = runner.run(plan, authorized=True)
    assert result['installed_stopped'] is True
    assert result['running_update_complete'] is False
    assert result['startup_authorized'] is False
    methods = [name for name, _ in backend.calls]
    assert max(i for i, name in enumerate(methods) if name == 'build') < methods.index('quiesce')
    quiesced = [args[0] for method, args in backend.calls if method == 'quiesce']
    assert quiesced == [r.id for r in reversed(plan.baseline[3:])]
    assert all(backend.rows[r.name] == r for r in plan.baseline[:3])
    assert all(backend.rows[n].state == 'created' for n in install.APPS)
    assert not any(name == 'restart_original' for name, _ in backend.calls)
    assert result['services_started'] is False


@pytest.mark.parametrize('failure', ['prepare', 'build'])
def test_preparation_failure_never_interrupts_originals(failure):
    plan, backend, receipt, runner = setup_runner(fail=failure)
    result = runner.run(plan, authorized=True)
    assert not result['installed_stopped']
    assert not any(name == 'quiesce' for name, _ in backend.calls)
    assert all(backend.rows[r.name] == r for r in plan.baseline)


@pytest.mark.parametrize('failure', ['rename', 'disconnect', 'create', 'verify_sources'])
@pytest.mark.parametrize('after', [False, True])
def test_replacement_failure_restores_only_original_applications(failure, after):
    plan, backend, receipt, runner = setup_runner(fail=failure, after=after)
    result = runner.run(plan, authorized=True)
    assert not result['installed_stopped'] and result['rollback_verified']
    assert result['rollback_exact_baseline'] is False
    assert result['rollback_service_health_verified'] is False
    assert result['services_started'] is True
    assert all(backend.rows[r.name] == r for r in plan.baseline[:3])
    assert all(backend.rows[r.name].id == r.id and backend.rows[r.name].state == 'running'
               for r in plan.baseline[3:])
    assert not any(row.attempt for row in backend.rows.values())
    assert [args[0] for method, args in backend.calls if method == 'restart_original'] == [r.id for r in plan.baseline[3:]]
    assert 'SYNTHETIC_SECRET' not in json.dumps(receipt.events)


@pytest.mark.parametrize('after', [False, True])
def test_unacknowledged_quiesce_is_not_claimed_or_restarted(after):
    plan, backend, receipt, runner = setup_runner(fail='quiesce', after=after)
    result = runner.run(plan, authorized=True)
    assert not result['installed_stopped'] and not result['rollback_verified']
    assert result['unresolved_quiesce'] == [install.APPS[-1]]
    assert not any(method == 'restart_original' for method, _ in backend.calls)
    assert not any(method in {'rename', 'disconnect', 'create', 'remove'} for method, _ in backend.calls)
    assert backend.rows[install.APPS[-1]].state == ('exited' if after else 'running')


def test_second_quiesce_failure_recovers_acknowledged_first_only():
    plan, backend, receipt, runner = setup_runner()
    original = backend.quiesce
    count = 0
    def quiesce(cid):
        nonlocal count
        count += 1
        if count == 2:
            raise RuntimeError('synthetic lost acknowledgment')
        return original(cid)
    backend.quiesce = quiesce
    result = runner.run(plan, authorized=True)
    assert not result['rollback_verified']
    assert result['unresolved_quiesce'] == [install.APPS[-2]]
    # The dependent orchestrator must not be restarted while memory's outcome
    # remains unresolved, even though its own interruption was acknowledged.
    assert not any(method == 'restart_original' for method, _ in backend.calls)


def test_storage_drift_prevents_further_mutation():
    plan, backend, receipt, runner = setup_runner()
    original = backend.quiesce
    def quiesce(cid):
        result = original(cid)
        row = plan.baseline[0]
        backend.rows[row.name] = replace(row, image='sha256:' + '0' * 64)
        return result
    backend.quiesce = quiesce
    result = runner.run(plan, authorized=True)
    assert not result['installed_stopped'] and not result['rollback_verified']
    assert not any(method in {'rename', 'disconnect', 'create', 'remove', 'restart_original'}
                   for method, _ in backend.calls)


def test_stale_application_refused_before_signal():
    plan, backend, receipt, runner = setup_runner()
    before = plan.baseline[-1]
    backend.rows[before.name] = replace(before, started='another-owner')
    result = runner.run(plan, authorized=True)
    assert not result['installed_stopped']
    assert not any(method == 'quiesce' for method, _ in backend.calls)


def test_restart_failure_does_not_start_dependents():
    plan, backend, receipt, runner = setup_runner(fail='create')
    backend.restart_original = lambda cid: False
    result = runner.run(plan, authorized=True)
    assert not result['rollback_verified']
    assert not runner.restored
    assert result['services_started'] is None
    assert result['unresolved_restart'] == [install.APPS[0]]


def test_lost_restart_ack_does_not_claim_no_start_or_start_dependents():
    plan, backend, receipt, runner = setup_runner(fail='create')
    original = backend.restart_original
    def lost(cid):
        original(cid)
        raise TimeoutError('SYNTHETIC_SECRET')
    backend.restart_original = lost
    result = runner.run(plan, authorized=True)
    assert not result['rollback_verified']
    assert result['services_started'] is None
    assert result['unresolved_restart'] == [install.APPS[0]]
    assert backend.rows[install.APPS[0]].state == 'running'
    assert all(backend.rows[n].state == 'exited' for n in install.APPS[1:])


@pytest.mark.parametrize('index', [0, 2])
@pytest.mark.parametrize('field', ['state', 'started', 'image'])
def test_observed_restored_prerequisite_drift_blocks_dependent_starts(index, field):
    plan, backend, receipt, runner = setup_runner(fail='create')
    inventory = backend.inventory
    target = install.APPS[index]
    drifted = False
    def changed_inventory():
        nonlocal drifted
        if target in runner.restored and not drifted:
            drifted = True
            row = backend.rows[target]
            backend.rows[target] = replace(row, **{field: {
                'state': 'exited', 'started': 'another-owner', 'image': 'sha256:' + '0' * 64,
            }[field]})
        return inventory()
    backend.inventory = changed_inventory
    result = runner.run(plan, authorized=True)
    assert drifted and not result['rollback_verified']
    assert [args[0] for method, args in backend.calls if method == 'restart_original'] == [
        r.id for r in plan.baseline[3:4 + index]]


def test_metadata_rejection_preserves_diagnostic_before_rollback():
    plan, backend, receipt, runner = setup_runner()
    create = backend.create
    def changed(name, image):
        result = create(name, image)
        backend.rows[name] = replace(backend.rows[name], configured_metadata='0' * 64)
        return result
    backend.create = changed
    backend.replacement_diagnostics = lambda *args: {'available': False}
    result = runner.run(plan, authorized=True)
    assert not result['installed_stopped'] and result['rollback_verified']
    phases = [event['phase'] for event in receipt.events]
    assert phases.index('replacement_metadata_diagnostic') < phases.index('remove_replacement_intended')


def test_shared_deadline_preserves_recovery_reserve():
    plan, backend, receipt, runner = setup_runner()
    now = [0]
    runner.clock = lambda: now[0]
    original = backend.build
    def build(name):
        result = original(name)
        now[0] = 421
        return result
    backend.build = build
    result = runner.run(plan, authorized=True)
    assert runner.end == 600 and runner.work_end == 420
    assert not result['installed_stopped']
    assert not any(method == 'quiesce' for method, _ in backend.calls)


def test_one_shot_and_authorization_required():
    plan, backend, receipt, runner = setup_runner()
    with pytest.raises(core.Refused):
        runner.run(plan)
    assert backend.calls == []
    runner.run(plan, authorized=True)
    with pytest.raises(core.Refused):
        runner.run(plan, authorized=True)


def test_cli_refuses_v4_application_before_native_backend(tmp_path, monkeypatch):
    data = install.canonical(running_manifest())
    path = tmp_path / 'synthetic.json'
    path.write_bytes(data)
    import scripts.research.companion_install_docker as native
    monkeypatch.setattr(native, 'DockerInstallBackend', lambda *a, **kw: pytest.fail('native backend must not be constructed'))
    result = install.main(['--manifest', str(path), '--reviewed-manifest-sha256', hashlib.sha256(data).hexdigest(),
                           '--apply-install', '--receipt', str(tmp_path / 'must-not-exist.jsonl')])
    assert result == 1
    assert not (tmp_path / 'must-not-exist.jsonl').exists()
