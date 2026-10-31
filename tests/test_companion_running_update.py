"""Shared-deadline integration with synthetic external state only."""
from dataclasses import replace
import json
import io
from types import SimpleNamespace

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from tests.test_companion_existing_controller import probe
from tests.test_companion_running_storage import setup_runner


class Runtime:
    def __init__(self, backend):
        self.backend = backend
        self.compatibility_result = dict.fromkeys(core.COMPATIBILITY, True)
        self.storage_result = dict.fromkeys(('postgres', 'qdrant', 'minio', 'namespaces'), True)
        self.health_result = dict.fromkeys(install.APPS, True)
        self.evidence_result = dict.fromkeys(core.EVIDENCE, True)
        self.response = probe()
        self.response['raw']['current_cause'] = 'SYNTHETIC_PRIVATE_PAYLOAD'
        self.response['diagnostics'] = [{'route': 'companion', 'stage': 'transport',
                                         'outcome': 'json_received', 'http_status': 200,
                                         'secret': 'SYNTHETIC_PRIVATE_PAYLOAD'}]

    def inventory(self):
        return self.backend.effect('runtime_inventory', lambda: {
            name: install.Installer._runtime_container(row) for name, row in self.backend.rows.items()})

    def compatibility(self, baseline):
        assert set(core.TARGETS).issubset(baseline)
        assert all(baseline[n].state == 'created' for n in install.APPS)
        return self.backend.effect('runtime_compatibility', lambda: self.compatibility_result)

    def storage_checks(self):
        return self.backend.effect('runtime_storage', lambda: self.storage_result)

    def start(self, cid):
        def change():
            name, before = next((name, row) for name, row in self.backend.rows.items() if row.id == cid)
            assert name in install.APPS and before.state == 'created'
            self.backend.rows[name] = replace(before, state='running', started='replacement-start')
        return self.backend.effect('runtime_start', change, cid)

    def health_checks(self):
        return self.backend.effect('runtime_health', lambda: self.health_result)

    def explain(self):
        return self.backend.effect('runtime_explain', lambda: self.response)

    def verify_evidence(self, raw):
        assert raw is self.response['raw']
        return self.backend.effect('runtime_evidence', lambda: self.evidence_result)


def harness(**kwargs):
    plan, backend, receipt, runner = setup_runner(**kwargs)
    def quiesce(expected):
        def change():
            before = install.Snapshot.from_record(expected)
            assert backend.rows[before.name] == before and before.state == 'running'
            backend.rows[before.name] = replace(before, state='exited')
            return True
        return backend.effect('quiesce_replacement', change, expected['id'])
    def remove(expected):
        def change():
            before = install.Snapshot.from_record(expected)
            assert backend.rows[before.name] == before and before.state == 'exited'
            del backend.rows[before.name]
        return backend.effect('remove_stopped_replacement', change, expected['id'])
    backend.quiesce_replacement = quiesce
    backend.remove_stopped_replacement = remove
    return plan, backend, receipt, runner, Runtime(backend)


def run(h):
    plan, _, _, runner, runtime = h
    return runner.run(plan, authorized=True, runtime=runtime, startup_authorized=True)


def assert_originals_restored(plan, backend):
    assert all(backend.rows[r.name] == r for r in plan.baseline[:3])
    assert all(backend.rows[r.name].id == r.id and backend.rows[r.name].state == 'running'
               for r in plan.baseline[3:])
    assert not any(row.attempt for row in backend.rows.values())


def test_explicit_startup_authorization_required_before_any_operation():
    plan, backend, _, runner, runtime = harness()
    with pytest.raises(core.Refused):
        runner.run(plan, authorized=True, runtime=runtime)
    assert backend.calls == []


def test_shared_update_starts_only_four_owned_apps_and_queries_once():
    h = harness()
    plan, backend, receipt, runner, _ = h
    result = run(h)
    assert result['running_update_complete'] and result['query_passed']
    assert not result['installed_stopped'] and result['startup_authorized']
    assert result['deferred_startup_policies'] == []
    assert runner.end == pytest.approx(runner.work_end + 180)
    assert all(backend.rows[r.name] == r for r in plan.baseline[:3])
    assert [args[0] for method, args in backend.calls if method == 'runtime_start'] == [
        backend.rows[n].id for n in install.APPS]
    assert sum(method == 'runtime_explain' for method, _ in backend.calls) == 1
    assert not any(method in {'quiesce_replacement', 'restart_original'} for method, _ in backend.calls)
    assert 'SYNTHETIC_PRIVATE_PAYLOAD' not in json.dumps(receipt.events)
    assert sum(event['phase'] == 'query_diagnostics' for event in receipt.events) == 1


@pytest.mark.parametrize('gate', ['compatibility', 'storage', 'health', 'evidence'])
def test_false_acceptance_gate_rolls_back_without_retry(gate):
    h = harness()
    plan, backend, _, _, runtime = h
    result_map = getattr(runtime, {'compatibility':'compatibility_result', 'storage':'storage_result',
                                  'health':'health_result', 'evidence':'evidence_result'}[gate])
    result_map[next(iter(result_map))] = False
    result = run(h)
    assert not result['running_update_complete'] and result['rollback_verified']
    assert_originals_restored(plan, backend)
    assert sum(method == 'runtime_explain' for method, _ in backend.calls) == (gate == 'evidence')


def test_compatibility_diagnostics_precede_cleanup_and_discard_private_values():
    h = harness()
    _, _, receipt, _, runtime = h
    runtime.compatibility_result['installed_source'] = 'SYNTHETIC_PRIVATE_PAYLOAD'
    runtime.compatibility_result['private_unexpected_key'] = 'SYNTHETIC_SECRET'
    result = run(h)
    assert not result['running_update_complete'] and result['rollback_verified']
    event = next(e for e in receipt.events if e['phase'] == 'runtime_compatibility_checks')
    evidence = event['installation_evidence']
    assert evidence['shape_valid'] is False and evidence['checks']['installed_source'] is False
    assert set(evidence['checks']) == core.COMPATIBILITY
    assert all(type(value) is bool for value in evidence['checks'].values())
    assert receipt.events.index(event) < next(i for i, e in enumerate(receipt.events)
                                             if e['phase'] == 'remove_replacement_intended')
    assert 'SYNTHETIC_PRIVATE_PAYLOAD' not in json.dumps(receipt.events)
    assert 'SYNTHETIC_SECRET' not in json.dumps(receipt.events)


@pytest.mark.parametrize('precondition', [
    {'predicate': 'preservation', 'target': 'phase1-memory'},
    {'predicate': 'SYNTHETIC_SECRET', 'target': 'phase1-memory'},
    {'predicate': ['SYNTHETIC_SECRET'], 'target': {'raw': 'SYNTHETIC_SECRET'}},
])
def test_v2_diagnostic_envelope_is_allowlisted_before_cleanup(precondition):
    h = harness()
    _, _, receipt, _, runtime = h
    flags = dict.fromkeys(core.COMPATIBILITY, False)
    runtime.compatibility_result = {'checks': flags, 'precondition': precondition}
    result = run(h)
    assert not result['running_update_complete'] and result['rollback_verified']
    event = next(e for e in receipt.events if e['phase'] == 'runtime_compatibility_checks')
    evidence = event['installation_evidence']
    assert evidence['precondition'] == (precondition if precondition['predicate'] == 'preservation' else None)
    assert evidence['false_meaning'] == 'not_established_or_not_evaluated'
    assert 'SYNTHETIC_SECRET' not in json.dumps(receipt.events)


def test_compatibility_exception_is_recorded_without_exception_text_before_cleanup():
    h = harness(fail='runtime_compatibility')
    _, _, receipt, _, _ = h
    result = run(h)
    assert not result['running_update_complete'] and result['rollback_verified']
    event = next(e for e in receipt.events if e['phase'] == 'runtime_compatibility_exception')
    assert event['installation_evidence'] == {'outcome': 'exception_or_timeout'}
    assert receipt.events.index(event) < next(i for i, e in enumerate(receipt.events)
                                             if e['phase'] == 'remove_replacement_intended')
    assert 'SYNTHETIC_SECRET' not in json.dumps(receipt.events)


@pytest.mark.parametrize('failure', ['runtime_inventory', 'runtime_compatibility', 'runtime_storage',
                                    'runtime_health', 'runtime_explain', 'runtime_evidence'])
@pytest.mark.parametrize('after', [False, True])
def test_runtime_failures_use_same_recovery_and_never_repeat_query(failure, after):
    h = harness(fail=failure, after=after)
    plan, backend, receipt, _, _ = h
    result = run(h)
    assert not result['running_update_complete'] and result['rollback_verified']
    assert_originals_restored(plan, backend)
    assert sum(method == 'runtime_explain' for method, _ in backend.calls) <= 1
    assert 'SYNTHETIC_PRIVATE_PAYLOAD' not in json.dumps(receipt.events)
    assert 'SYNTHETIC_SECRET' not in json.dumps(receipt.events)


def test_failed_start_before_effect_is_resolved_only_by_owned_resource_removal():
    h = harness(fail='runtime_start')
    plan, backend, receipt, _, _ = h
    result = run(h)
    assert result['rollback_verified']
    assert result['unresolved_replacement_start'] == []
    assert_originals_restored(plan, backend)
    assert any(e['phase'] == 'pending_start_resolved_by_resource_removal' for e in receipt.events)


def test_unacknowledged_started_replacement_is_not_stopped_as_owned():
    h = harness(fail='runtime_start', after=True)
    _, backend, _, _, _ = h
    result = run(h)
    assert not result['rollback_verified'] and result['services_started'] is None
    assert result['unresolved_replacement_start'] == [install.APPS[0]]
    assert not any(method == 'quiesce_replacement' for method, _ in backend.calls)


@pytest.mark.parametrize('after', [False, True])
def test_cleanup_ack_failure_is_not_retried_or_claimed_recovered(after):
    h = harness(fail='quiesce_replacement', after=after)
    _, backend, _, _, runtime = h
    runtime.health_result[install.APPS[0]] = False
    result = run(h)
    assert not result['rollback_verified']
    assert result['unresolved_replacement_cleanup'] == [install.APPS[-1]]
    calls = [args[0] for method, args in backend.calls if method == 'quiesce_replacement']
    assert len(calls) == len(set(calls))


@pytest.mark.parametrize('after', [False, True])
def test_removal_failure_retains_cleanup_uncertainty(after):
    h = harness(fail='remove_stopped_replacement', after=after)
    _, _, _, _, runtime = h
    runtime.health_result[install.APPS[0]] = False
    result = run(h)
    assert not result['rollback_verified']
    assert result['unresolved_replacement_cleanup'] == [install.APPS[-1]]


def test_renamed_unacknowledged_running_replacement_cannot_hide_from_recovery_gate():
    h = harness(fail='runtime_start', after=True)
    plan, backend, _, _, runtime = h
    start = runtime.start
    def external_rename(cid):
        try:
            return start(cid)
        except TimeoutError:
            row = backend.rows.pop(install.APPS[0])
            backend.rows['renamed-outside-selected-names'] = replace(row, name='renamed-outside-selected-names')
            raise
    runtime.start = external_rename
    inventory = backend.inventory
    def selected_inventory():
        original_ids = {r.id for r in plan.baseline}
        names = set(core.TARGETS) | {plan.rollback_name(n) for n in install.APPS}
        return [row for row in inventory() if row['id'] in original_ids or row['name'] in names]
    backend.inventory = selected_inventory
    result = run(h)
    assert not result['rollback_verified']
    assert result['unresolved_replacement_start'] == [install.APPS[0]]
    assert backend.rows['renamed-outside-selected-names'].state == 'running'


@pytest.mark.parametrize('after', [False, True])
def test_unacknowledged_creation_stays_unresolved(after):
    h = harness(fail='create', after=after)
    result = run(h)
    assert not result['running_update_complete'] and not result['rollback_verified']
    assert result['unresolved_creation'] == [install.APPS[0]]


def test_diagnostics_precede_rejection_and_cleanup():
    h = harness()
    _, _, receipt, _, runtime = h
    runtime.response['raw']['execution_disabled'] = False
    result = run(h)
    assert not result['query_passed'] and result['rollback_verified']
    phases = [event['phase'] for event in receipt.events]
    assert phases.index('query_diagnostics') < phases.index('installation_failed')
    assert phases.index('installation_failed') < phases.index('replacement_quiesce_intended')


def test_query_timeout_spends_budget_without_resetting_cleanup_deadline():
    h = harness()
    _, backend, receipt, runner, runtime = h
    now = [0]
    runner.clock = lambda: now[0]
    explain = runtime.explain
    def too_late():
        result = explain()
        now[0] = 421
        return result
    runtime.explain = too_late
    result = run(h)
    assert runner.end == 600 and runner.work_end == 420
    assert not result['query_passed'] and result['rollback_verified']
    assert sum(method == 'runtime_explain' for method, _ in backend.calls) == 1
    assert any(e['phase'] == 'query_failure_diagnostics' for e in receipt.events)


@pytest.mark.parametrize('persistent', [False, True])
def test_runtime_pin_mismatch_refuses_before_start_and_requires_trustworthy_recovery_observation(persistent):
    h = harness()
    _, backend, _, _, runtime = h
    original = runtime.inventory
    def mismatch():
        rows = original()
        if persistent or rows[install.APPS[0]].state == 'created':
            rows[install.APPS[0]] = replace(rows[install.APPS[0]], id='0' * 64)
        return rows
    runtime.inventory = mismatch
    result = run(h)
    assert not result['query_passed']
    assert result['rollback_verified'] is (not persistent)
    assert not any(method == 'runtime_start' for method, _ in backend.calls)


def test_started_prerequisite_drift_prevents_next_start_and_query():
    h = harness()
    _, backend, _, runner, runtime = h
    inventory = backend.inventory
    changed = False
    def drift():
        nonlocal changed
        if install.APPS[0] in runner.replacement_started and not changed:
            changed = True
            row = backend.rows[install.APPS[0]]
            backend.rows[install.APPS[0]] = replace(row, started='external-restart')
        return inventory()
    backend.inventory = drift
    result = run(h)
    assert not result['query_passed'] and not result['rollback_verified']
    assert sum(method == 'runtime_start' for method, _ in backend.calls) == 1
    assert not any(method == 'runtime_explain' for method, _ in backend.calls)


def test_integration_reuses_actual_dashboard_probe_without_primary_or_secret_receipt(monkeypatch):
    from dashboard.services.views import _shared_http as http, _shared_signals as signals, market_view
    from tests.test_companion_existing_controller import response
    h = harness()
    _, backend, receipt, _, runtime = h
    calls = []
    class Reply(io.BytesIO):
        status = 200
    class Opener:
        def open(self, req, timeout):
            assert req.full_url == 'http://127.0.0.1:8002/v1/explain'
            assert req.get_header('Authorization') == 'Bearer SYNTHETIC_ONLY'
            assert req.get_header('X-cryptkeep-probe') == core.PROTOCOL
            calls.append(req.full_url)
            return Reply(json.dumps(response()).encode())
    monkeypatch.setattr(core, '_CHILD_CONTEXT', True)
    monkeypatch.setattr(http.urllib.request, 'build_opener', lambda *a: Opener())
    monkeypatch.setattr(http.urllib.request, 'urlopen', lambda *a, **kw: pytest.fail('primary must not be called'))
    stub = SimpleNamespace(_default_explain_payload=lambda *a: {'assistant_status': {'provider': 'dashboard_fallback'}},
        _explain_mentions_foreign_asset=signals._explain_mentions_foreign_asset,
        _request_envelope=http._request_envelope, _request_envelope_from_base=http._request_envelope_from_base,
        _read_mock_envelope=lambda *a: None, PHASE1_ORCHESTRATOR_URL='http://must-not-use.invalid')
    monkeypatch.setattr(market_view, '_view_data', lambda: stub)
    def explain():
        runtime.response = core.dashboard_probe('SYNTHETIC_ONLY')
        return runtime.response
    runtime.explain = explain
    result = run(h)
    assert result['query_passed']
    assert calls == ['http://127.0.0.1:8002/v1/explain']
    assert 'SYNTHETIC_ONLY' not in json.dumps(receipt.events)
    assert http._PROBE.get() is None
