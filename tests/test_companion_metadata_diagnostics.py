"""Offline diagnostic-only comparisons; no Docker/socket or credential access."""
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from scripts.research import companion_metadata_diagnostics as diagnostic
from scripts.research import companion_install_docker as docker
from scripts.research import companion_installer as install
from tests.test_companion_installer import load, runner

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / 'docs/review_artifacts/companion_install_candidate_20261018/configured_v3'
PLAN_SHA = 'f5b044858c3d40881239b77745d0b404c4ac05d2f35a6d043fed8f6ba934bf5f'


@pytest.fixture
def profile():
    raw = (SAVED / 'reviewed_configured_plan.json').read_bytes()
    plan = install.Plan.load(raw, PLAN_SHA)
    observations = json.loads((SAVED / 'capture/observation.json').read_bytes())['observations']
    data = diagnostic.make_profile(plan, PLAN_SHA, observations)
    encoded = json.dumps(data).encode()
    expected = diagnostic.Expectations.load(encoded, hashlib.sha256(encoded).hexdigest(), plan, PLAN_SHA)
    return plan, data, expected


def comparison(profile, field=None, value=None):
    plan, data, expected = profile
    row = copy.deepcopy(data['applications'][0]['expected'])
    if field:
        row[field] = value
    result = expected.compare(plan.applications[0]['name'], row,
                              diagnostic.fingerprint(row, dict(plan.network_bindings)))
    return row, result


def test_saved_expected_projection_matches_all_four_reviewed_gate_digests(profile):
    plan, data, expected = profile
    assert len(data['applications']) == 4
    for record, app in zip(data['applications'], plan.applications):
        result = expected.compare(app['name'], record['expected'], app['replacement_configured_metadata'])
        assert result['aggregate_matches'] and all(result['fields'].values())
        assert not result['interaction_unresolved']


@pytest.mark.parametrize('field,value', [
    ('workdir', 'SYNTHETIC_PRIVATE_VALUE'), ('command', ['SYNTHETIC_PRIVATE_VALUE']),
    ('healthcheck', {'Test': ['CMD', 'SYNTHETIC_PRIVATE_VALUE']}),
    ('user', 'SYNTHETIC_PRIVATE_VALUE'), ('memory', 100),
    ('privileged', True), ('has_security_options', True), ('dns', ['192.0.2.1'])])
def test_fixed_field_only_booleans_no_values_or_value_hashes(profile, field, value):
    _, result = comparison(profile, field, value)
    assert result['aggregate_matches'] is False
    assert [k for k, v in result['fields'].items() if not v] == [field]
    text = json.dumps(result)
    assert 'SYNTHETIC_PRIVATE_VALUE' not in text
    assert hashlib.sha256(json.dumps(value).encode()).hexdigest() not in text


def test_flag_order_is_detected_not_silently_normalized(profile):
    flags = list(reversed(profile[1]['applications'][0]['expected']['flags']))
    _, result = comparison(profile, 'flags', flags)
    assert not result['aggregate_matches'] and not result['fields']['flags']
    assert result['flags_order_only']


def test_alias_order_and_configured_placeholder_follow_unchanged_gate(profile):
    plan, data, expected = profile
    row = copy.deepcopy(data['applications'][0]['expected'])
    for net in row['networks'].values():
        net['Aliases'] = list(reversed(net['Aliases']))
        net['NetworkID'] = ''
        net['IPAMConfig'] = {}
    result = expected.compare(plan.applications[0]['name'], row,
                              diagnostic.fingerprint(row, dict(plan.network_bindings)))
    assert result['aggregate_matches'] and all(result['fields'].values())


@pytest.mark.parametrize('change', ['profile_hash', 'plan_binding', 'expected_value', 'extra_secret_key', 'duplicate_key'])
def test_unbound_or_modified_profile_refused(profile, change):
    plan, data, _ = profile
    data = copy.deepcopy(data)
    if change == 'plan_binding':
        data['plan_sha256'] = '0' * 64
    elif change == 'expected_value':
        data['applications'][0]['expected']['workdir'] = 'wrong'
    elif change == 'extra_secret_key':
        data['applications'][0]['expected']['SERVICE_TOKEN'] = 'SYNTHETIC_ONLY'
    raw = json.dumps(data).encode()
    if change == 'duplicate_key':
        raw = raw.replace(b'{', b'{"schema":"duplicate",', 1)
    pin = '0' * 64 if change == 'profile_hash' else hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match='^metadata_diagnostics_refused$'):
        diagnostic.Expectations.load(raw, pin, plan, PLAN_SHA)


def test_observed_snapshot_change_and_raw_environment_payload_refused(profile):
    plan, data, expected = profile
    row = copy.deepcopy(data['applications'][0]['expected'])
    with pytest.raises(ValueError):
        expected.compare(plan.applications[0]['name'], row, '0' * 64)
    row['flags'] = [{'key': 'SERVICE_TOKEN', 'ok': 'SYNTHETIC_ONLY'}]
    with pytest.raises(ValueError):
        expected.compare(plan.applications[0]['name'], row, '0' * 64)


@pytest.mark.parametrize('field,value', [('unexpected', 'SYNTHETIC_ONLY'), ('fields', {'secret': True}),
                                        ('available', 1), ('aggregate_matches', 'secret')])
def test_arbitrary_backend_report_never_enters_receipt(profile, field, value):
    _, result = comparison(profile)
    result[field] = value
    with pytest.raises(ValueError):
        diagnostic.validate_report(result)


def test_concrete_backend_uses_same_inspect_and_checks_identity(profile, tmp_path):
    plan, data, expected = profile
    backend = docker.DockerInstallBackend(plan, tmp_path, metadata_expectations=expected)
    name = plan.applications[0]['name']
    identity = '9' * 64
    row = {**data['applications'][0]['expected'], 'id': identity, 'name': '/' + name,
           'state': 'created', 'started': '0001-01-01T00:00:00Z', 'restarts': 0,
           'restart_policy': 'no', 'attempt': plan.attempt}
    calls = []
    def command(args):
        calls.append(args)
        return json.dumps(row).encode()
    backend._command = command
    result = backend.replacement_diagnostics(name, identity, plan.applications[0]['replacement_configured_metadata'])
    assert result['aggregate_matches']
    assert calls == [('container', 'inspect', '--format', docker.FORMAT, identity)]
    row['attempt'] = 'foreign'
    with pytest.raises(Exception):
        backend.replacement_diagnostics(name, identity, '0' * 64)


def test_no_profile_makes_no_diagnostic_command(tmp_path):
    backend = docker.DockerInstallBackend(load(), tmp_path)
    backend._command = lambda *a, **k: pytest.fail('unexpected command')
    assert backend.replacement_diagnostics('anything', 'anything', 'anything') == diagnostic.unavailable()


@pytest.mark.parametrize('mode', ['valid', 'exception', 'malicious_report', 'wrong_aggregate', 'receipt_failure'])
def test_installer_records_before_cleanup_and_never_bypasses_gate(profile, mode):
    plan, backend, receipt, run = runner()
    create = backend.create
    def changed(name, image):
        create(name, image)
        backend.rows[name] = replace(backend.rows[name], metadata='0' * 64)
    backend.create = changed
    _, report = comparison(profile, 'workdir', 'SYNTHETIC_PRIVATE_VALUE')
    def diagnose(*args):
        if mode == 'exception':
            raise ValueError('SYNTHETIC_PRIVATE_VALUE')
        if mode == 'malicious_report':
            return {**report, 'secret': 'SYNTHETIC_PRIVATE_VALUE'}
        if mode == 'wrong_aggregate':
            return {**report, 'aggregate_matches': True}
        return report
    backend.replacement_diagnostics = diagnose
    write = receipt.write
    if mode == 'receipt_failure':
        def failing(event):
            if event['phase'] == 'replacement_metadata_diagnostic':
                raise OSError('SYNTHETIC_PRIVATE_VALUE')
            write(event)
        receipt.write = failing
    result = run.run(plan, authorized=True)
    assert not result['installed_stopped'] and result['rollback_verified']
    assert result['failure_stage'] == 'replacement_checks'
    assert not any(c[0] == 'verify_sources' for c in backend.calls)
    if mode != 'receipt_failure':
        event = next(e for e in receipt.events if e['phase'] == 'replacement_metadata_diagnostic')
        assert event['installation_evidence']['available'] is (mode == 'valid')
        assert receipt.events.index(event) < next(i for i,e in enumerate(receipt.events)
                                               if e['phase'] == 'remove_replacement_intended')
    assert 'SYNTHETIC_PRIVATE_VALUE' not in json.dumps(receipt.events) + json.dumps(result)
    assert all(backend.rows.get(r.name) == r for r in plan.baseline)


def test_public_profile_path_boundary_refuses_unreviewed_locations(tmp_path, profile):
    plan, data, _ = profile
    path = tmp_path / 'public.json'
    raw = json.dumps(data).encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        diagnostic.read_profile(path, hashlib.sha256(raw).hexdigest(), plan, PLAN_SHA)


def test_cli_requires_paired_profile_arguments_before_any_operation(tmp_path, capsys):
    path = tmp_path / 'manifest.json'
    from tests.test_companion_installer import manifest
    raw = install.canonical(manifest())
    path.write_bytes(raw)
    assert install.main(['--manifest', str(path), '--reviewed-manifest-sha256', hashlib.sha256(raw).hexdigest(),
                         '--metadata-expectations', str(tmp_path / 'missing.json')]) == 1
    assert json.loads(capsys.readouterr().out)['reason'] == 'installation_refused'
