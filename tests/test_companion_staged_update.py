"""Offline two-phase state-machine proof, not a Docker/runtime result."""
from dataclasses import asdict, replace
import hashlib
import json

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from scripts.research import companion_staged_update as staged
from tests.test_companion_installer import Inline, Receipt, load
from tests.test_companion_running_storage import RunningBackend, running_manifest
from tests.test_companion_running_update import Runtime


class Backend(RunningBackend):
    def inventory(self, extra_ids=()):
        assert len(extra_ids) <= 4
        return super().inventory()

    def create_staged(self, name, image):
        def change():
            old = next(r for r in self.plan.baseline if r.name == name)
            row = replace(old, name=self.plan.staged_name(name), id=f'{100 + install.APPS.index(name):064x}',
                          image=image, state='created', started=core.NEVER_STARTED[0],
                          attempt=self.plan.attempt, metadata='7' * 64, configured_metadata='7' * 64)
            self.rows[row.name] = row
            return row.id
        return self.effect('create_staged', change, name, image)

    def verify_staged_sources(self, name, expected):
        def check():
            row = install.Snapshot.from_record(expected)
            assert self.rows[row.name] == row and row.state == 'created'
            return True
        return self.effect('verify_staged_sources', check, name)

    def remove_staged(self, name, expected):
        def change():
            row = install.Snapshot.from_record(expected)
            assert row == self.rows[row.name] and row.state == 'created'
            del self.rows[row.name]
        return self.effect('remove_staged', change, name)

    def _change_stage(self, method, expected, fn):
        def change():
            before = install.Snapshot.from_record(expected)
            assert self.rows[before.name] == before
            del self.rows[before.name]
            after = fn(before)
            self.rows[after.name] = after
        return self.effect(method, change, expected['id'])

    def disconnect_staged(self, name, expected):
        return self._change_stage('disconnect_staged', expected,
            lambda r: replace(r, networks=(), configured_networks=(), network_evidence=(),
                              metadata='6' * 64, configured_metadata='6' * 64))

    def rename_staged(self, name, expected, new_name):
        return self._change_stage('rename_staged', expected, lambda r: replace(r, name=new_name))

    def connect_staged(self, name, expected):
        return self._change_stage('connect_staged', expected,
            lambda r: replace(r, networks=('',), configured_networks=('e' * 64,),
                              network_evidence=(('synthetic', 'e' * 64, 'configured_only'),),
                              metadata='8' * 64, configured_metadata='c' * 64))

    def quiesce_replacement(self, expected):
        def change():
            before = install.Snapshot.from_record(expected)
            assert self.rows[before.name] == before and before.state == 'running'
            self.rows[before.name] = replace(before, state='exited')
            return True
        return self.effect('quiesce_replacement', change, expected['id'])

    def remove_stopped_replacement(self, expected):
        def change():
            before = install.Snapshot.from_record(expected)
            assert self.rows[before.name] == before and before.state == 'exited'
            del self.rows[before.name]
        return self.effect('remove_stopped_replacement', change, expected['id'])


class StagedRuntime(Runtime):
    def configured_compatibility(self, baseline, bindings):
        assert bindings == dict(self.backend.plan.network_bindings)
        return self.compatibility(baseline)

    def recipient_checks(self):
        assert all(self.backend.rows[n].state == 'running' for n in core.TARGETS)
        return self.backend.effect('runtime_recipients', lambda: {'recipient_bindings': True})

    def staged_checks(self, expected):
        assert set(expected) == set(core.TARGETS)
        assert all(expected[n].name == self.backend.plan.staged_name(n) for n in install.APPS)
        assert all(self.backend.rows[n].state == 'running' for n in core.TARGETS)
        return self.backend.effect('runtime_staged_checks', lambda: {
            k: v for k, v in self.compatibility_result.items() if k != 'recipient_bindings'})


def harness(**kwargs):
    data = running_manifest()
    data['schema'] = 'companion-staged-update-v5'
    plan = load(data)
    backend, receipt = Backend(plan, **kwargs), Receipt()
    runner = install.Installer(backend, receipt, executor=Inline())
    return plan, backend, receipt, runner


def reviewed(plan, evidence):
    raw = install.canonical(evidence)
    record = {'schema': 'companion-preparation-review-v1', 'decision': 'ACCEPTED_WITH_RISK',
              'reviewer': 'SYNTHETIC_EXTERNAL_ONLY', 'manifest_sha256': plan.manifest_sha256,
              'evidence_sha256': hashlib.sha256(raw).hexdigest()}
    review = install.canonical(record)
    return staged.ReviewedPreparation.load(raw, review, hashlib.sha256(review).hexdigest(), plan)


def prepared_harness(**kwargs):
    plan, backend, receipt, preparation = harness()
    result = preparation.prepare_staged(plan, authorized=True)
    assert result['state'] == 'READY_FOR_INDEPENDENT_REVIEW'
    approval = reviewed(plan, result['preparation_evidence'])
    backend.calls.clear()
    backend.fail = kwargs.get('fail')
    backend.after = kwargs.get('after', False)
    runner = install.Installer(backend, receipt, executor=Inline())
    return plan, backend, receipt, runner, StagedRuntime(backend), approval


def cutover(h):
    plan, _, _, runner, runtime, approval = h
    return runner.run(plan, authorized=True, runtime=runtime, startup_authorized=True, prepared=approval)


def test_prepare_records_actual_ids_without_interrupting_originals_or_approving_them():
    plan, backend, receipt, runner = harness()
    result = runner.prepare_staged(plan, authorized=True)
    assert result['state'] == 'READY_FOR_INDEPENDENT_REVIEW'
    assert all(backend.rows[r.name] == r for r in plan.baseline)
    assert all(r['state'] == 'created' for r in result['preparation_evidence']['replacements'])
    assert {r['id'] for r in result['preparation_evidence']['replacements']} == runner.known_replacement_ids
    assert not any(m in {'quiesce', 'rename', 'disconnect', 'runtime_start'} for m, _ in backend.calls)
    assert runner.end - runner.work_end == 120
    assert 'decision' not in result['preparation_evidence']
    assert 'SYNTHETIC_SECRET' not in json.dumps(receipt.events)


@pytest.mark.parametrize('method', ['prepare', 'build', 'create_staged', 'verify_staged_sources'])
@pytest.mark.parametrize('after', [False, True])
def test_prepare_failure_keeps_originals_and_does_not_adopt_unknown_creation(method, after):
    plan, backend, _, runner = harness(fail=method, after=after)
    result = runner.prepare_staged(plan, authorized=True)
    assert result['state'] == 'INCOMPLETE'
    assert all(backend.rows[r.name] == r for r in plan.baseline)
    assert not any(m == 'quiesce' for m, _ in backend.calls)
    if method == 'create_staged':
        assert result['unresolved_creation'] == [install.APPS[0]]
        assert not result['cleanup_verified']
        assert not any(m == 'remove_staged' for m, _ in backend.calls)
    else:
        assert result['cleanup_verified']


@pytest.mark.parametrize('change', ['hash', 'decision', 'duplicate', 'started', 'id', 'manifest', 'extra'])
def test_external_review_and_prepared_evidence_are_bound(change):
    plan, _, _, runner = harness()
    result = runner.prepare_staged(plan, authorized=True)
    evidence = result['preparation_evidence']
    if change == 'hash':
        raw = install.canonical(evidence)
        with pytest.raises(core.Refused):
            staged.ReviewedPreparation.load(raw, b'{}', '0' * 64, plan)
        return
    if change == 'decision':
        raw = install.canonical(evidence)
        record = install.canonical({'schema': 'companion-preparation-review-v1', 'decision': 'READY_FOR_INDEPENDENT_REVIEW',
            'reviewer': 'fixture', 'manifest_sha256': plan.manifest_sha256,
            'evidence_sha256': hashlib.sha256(raw).hexdigest()})
        with pytest.raises(core.Refused):
            staged.ReviewedPreparation.load(raw, record, hashlib.sha256(record).hexdigest(), plan)
        return
    if change == 'duplicate':
        evidence['replacements'][1]['id'] = evidence['replacements'][0]['id']
    elif change == 'started':
        evidence['replacements'][0]['state'] = 'running'
    elif change == 'id':
        evidence['replacements'][0]['id'] = plan.baseline[0].id
    elif change == 'manifest':
        evidence['manifest_sha256'] = '0' * 64
    else:
        evidence['extra'] = True
    with pytest.raises(core.Refused):
        reviewed(plan, evidence)


def test_cutover_uses_reviewed_ids_without_rebuilding_and_queries_once():
    h = prepared_harness()
    plan, backend, receipt, runner, _, approval = h
    result = cutover(h)
    assert result['running_update_complete'] and result['prepared_ids_preserved']
    assert result['preparation_consumed'] and not result['preparation_reusable']
    assert {backend.rows[n].id for n in install.APPS} == {r.id for r in approval.replacements}
    assert all(backend.rows[r.name] == r for r in plan.baseline[:3])
    assert not any(m in {'build', 'create', 'create_staged'} for m, _ in backend.calls)
    methods = [m for m, _ in backend.calls]
    assert methods.count('prepare') == 1
    assert methods.index('prepare') < methods.index('quiesce')
    assert methods.index('runtime_staged_checks') < methods.index('quiesce')
    assert methods.count('runtime_explain') == 1
    assert methods.index('runtime_recipients') < methods.index('runtime_health') < methods.index('runtime_explain')
    assert runner.end - runner.work_end == 180
    assert 'SYNTHETIC_PRIVATE_PAYLOAD' not in json.dumps(receipt.events)


def test_review_wait_does_not_spend_the_separate_cutover_deadline():
    h = prepared_harness()
    runner = h[3]
    runner.clock = lambda: 100_000
    assert cutover(h)['running_update_complete']
    assert runner.end == 100_600 and runner.work_end == 100_420


@pytest.mark.parametrize('field,value', [('id', '9' * 64), ('image', 'sha256:' + '9' * 64),
    ('policy', 'always'), ('configured_metadata', '9' * 64), ('state', 'running')])
def test_changed_reviewed_resource_is_refused_before_interruption(field, value):
    h = prepared_harness()
    plan, backend, _, _, _, _ = h
    name = plan.staged_name(install.APPS[0])
    backend.rows[name] = replace(backend.rows[name], **{field: value})
    result = cutover(h)
    assert not result['running_update_complete'] and not result['preparation_consumed']
    assert not any(m == 'quiesce' for m, _ in backend.calls)
    assert all(backend.rows[r.name] == r for r in plan.baseline)


@pytest.mark.parametrize('gate', ['staged', 'storage'])
def test_preinterruption_policy_failure_preserves_staging(gate):
    h = prepared_harness()
    plan, backend, _, _, runtime, approval = h
    if gate == 'staged':
        runtime.compatibility_result[next(iter(core.COMPATIBILITY - {'recipient_bindings'}))] = False
    else:
        runtime.storage_result['namespaces'] = False
    result = cutover(h)
    assert not result['running_update_complete'] and not result['preparation_consumed']
    assert all(backend.rows[r.name] == r for r in plan.baseline)
    assert all(backend.rows[r.name] == r for r in approval.replacements)


def test_changed_engine_or_prerequisite_refuses_before_interruption():
    h = prepared_harness(fail='prepare')
    plan, backend, _, _, _, approval = h
    result = cutover(h)
    assert not result['running_update_complete'] and not result['preparation_consumed']
    assert not any(m in {'quiesce', 'build', 'create_staged'} for m, _ in backend.calls)
    assert all(backend.rows[r.name] == r for r in plan.baseline)
    assert all(backend.rows[r.name] == r for r in approval.replacements)


@pytest.mark.parametrize('failure', ['rename', 'disconnect', 'disconnect_staged', 'rename_staged',
    'connect_staged', 'verify_sources', 'runtime_health', 'runtime_explain', 'runtime_evidence'])
def test_cutover_failures_restore_originals_and_consume_review(failure):
    h = prepared_harness(fail=failure)
    plan, backend, _, _, _, _ = h
    result = cutover(h)
    assert not result['running_update_complete']
    assert result['rollback_verified'], (failure, result)
    assert result['preparation_consumed'] and not result['preparation_reusable']
    assert all(backend.rows[r.name] == r for r in plan.baseline[:3])
    assert all(backend.rows[r.name].id == r.id and backend.rows[r.name].state == 'running'
               for r in plan.baseline[3:])
    assert not any(r.attempt for r in backend.rows.values())
    assert sum(m == 'runtime_explain' for m, _ in backend.calls) <= 1


def test_unknown_start_is_not_claimed_as_owned_or_recovered():
    h = prepared_harness(fail='runtime_start', after=True)
    result = cutover(h)
    assert not result['rollback_verified'] and result['services_started'] is None
    assert result['unresolved_replacement_start'] == [install.APPS[0]]


def test_actual_recipient_check_cannot_be_replaced_by_configuration_proof():
    h = prepared_harness()
    h[4].recipient_checks = lambda: {'recipient_bindings': False}
    result = cutover(h)
    assert not result['running_update_complete'] and result['rollback_verified']
    assert not any(method in {'runtime_health', 'runtime_explain'} for method, _ in h[1].calls)


@pytest.mark.parametrize('failure', ['disconnect_staged', 'rename_staged', 'connect_staged'])
def test_lost_activation_acknowledgment_cannot_claim_false_recovery(failure):
    h = prepared_harness(fail=failure, after=True)
    plan, backend, _, _, _, approval = h
    result = cutover(h)
    assert not result['running_update_complete']
    assert result['preparation_consumed']
    if result['rollback_verified']:
        assert not {r.id for r in approval.replacements}.intersection(r.id for r in backend.rows.values())
        assert all(backend.rows[r.name].id == r.id and backend.rows[r.name].state == 'running'
                   for r in plan.baseline[3:])
    else:
        assert result['unresolved_replacement_cleanup']


def test_unreviewed_same_attempt_resource_refuses_before_quiesce():
    h = prepared_harness()
    plan, backend, _, _, _, approval = h
    row = approval.replacements[0]
    backend.rows['unexpected'] = replace(row, name='unexpected', id='f' * 64)
    result = cutover(h)
    assert not result['running_update_complete']
    assert not any(m == 'quiesce' for m, _ in backend.calls)
    assert all(backend.rows[r.name] == r for r in plan.baseline)


def test_cutover_budget_does_not_reset_after_staged_preflight():
    h = prepared_harness()
    now = [0]
    h[3].clock = lambda: now[0]
    check = h[4].staged_checks
    def spend_budget(expected):
        result = check(expected)
        now[0] = 421
        return result
    h[4].staged_checks = spend_budget
    result = cutover(h)
    assert not result['running_update_complete']
    assert h[3].end == 600 and h[3].work_end == 420
    assert not any(m == 'quiesce' for m, _ in h[1].calls)


def test_direct_v5_run_requires_separate_review_and_startup_authority():
    plan, backend, receipt, runner = harness()
    with pytest.raises(core.Refused):
        runner.run(plan, authorized=True)
    assert not backend.calls
    with pytest.raises(core.Refused):
        runner.prepare_staged(plan)
    assert not backend.calls
