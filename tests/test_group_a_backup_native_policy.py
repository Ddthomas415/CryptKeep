"""Controller/policy source checks; never run downloaded native programs."""
import hashlib
import json
import time

import pytest

from scripts.research import probe_group_a_backup_native as probe
from services.control import group_a_backup_bundle as core
from services.control import group_a_backup_tools as tools
from tests.test_group_a_backup_tools import inputs as tool_inputs


@pytest.fixture
def staged(tool_inputs):
    digest = hashlib.sha256(tool_inputs['path'].read_bytes()).hexdigest()
    result = tools.prepare(tool_inputs['parent'], pins_path=tool_inputs['path'], pins_sha256=digest,
                           deadline=time.monotonic() + 10, fetch=tool_inputs['fetch'])
    return tool_inputs, result, digest


def verify(staged):
    inputs, result, digest = staged
    return probe.verify_tools(core.Path(result['directory']), result['receipt_sha256'],
                              inputs['path'], digest, time.monotonic() + 10)


def test_staged_tool_receipt_and_binary_identity(staged):
    paths, value = verify(staged)
    assert set(paths) == {'restic', 'rclone'}
    assert value['clients_executed'] is False
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in paths.values())


@pytest.mark.parametrize('mutation', ['binary', 'format_boolean', 'signature', 'path', 'unknown_field'])
def test_changed_or_ambiguous_tool_identity_refused(staged, mutation):
    inputs, result, digest = staged
    root = core.Path(result['directory'])
    if mutation == 'binary':
        (root / 'bin/restic').write_bytes(b'changed')
    else:
        path = root / 'TOOLCHAIN.json'
        value = json.loads(path.read_bytes())
        if mutation == 'format_boolean':
            value['format'] = True
        elif mutation == 'signature':
            value['signature_verified'] = True
        elif mutation == 'path':
            value['tools']['restic']['relative_path'] = '../../outside'
        else:
            value['private'] = 'SYNTHETIC-private'
        path.write_bytes(core._encode(value))
        result['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(core.BundleError):
        verify(staged)


def test_policy_is_deny_by_default_with_scoped_payload_access(tmp_path):
    tmp_path.chmod(0o700)
    text = probe.sandbox_profile(tmp_path)
    assert '(deny default)' in text and '(deny network*)' in text
    assert '(allow process-exec ' in text
    assert '(allow file-write* (subpath ' + json.dumps(str(tmp_path / 'work')) in text
    assert '/Users/' not in text
    assert '(subpath "/")' not in text
    assert 'outside-canary' not in text


def test_no_execute_flag_never_validates_or_starts_native_clients(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail('native preflight must not run')
    monkeypatch.setattr(probe, 'verify_tools', forbidden)
    assert probe.main(['--tools', '/nonexistent', '--receipt-sha256', 'a' * 64,
                       '--pins', '/nonexistent', '--pins-sha256', 'b' * 64]) == 1
    assert json.loads(capsys.readouterr().out)['clients_executed'] is False


def test_sandbox_failure_stops_before_crypto_commands_or_fixture(staged, tmp_path, monkeypatch):
    inputs, result, digest = staged
    parent = tmp_path / 'probe'
    parent.mkdir(mode=0o700)
    calls = []
    def command(argv, *args):
        calls.append(argv)
        return 1, b'', b'SYNTHETIC-private'
    monkeypatch.setattr(probe, '_command', command)
    def forbidden(*args, **kwargs):
        pytest.fail('fixture must not be built before sandbox preflight passes')
    monkeypatch.setattr(probe, '_fixture', forbidden)
    output = probe._worker(result['directory'], result['receipt_sha256'], str(inputs['path']), digest,
                           str(parent), time.monotonic() + 10)
    assert output == {'status': 'INCOMPLETE', 'phase': 'sandbox_positive', 'offsite_verified': False}
    assert len(calls) == 1 and calls[0][0] == '/bin/cat'
    assert 'SYNTHETIC-private' not in json.dumps(output)
    assert all((core.Path(result['directory']) / 'bin' / name).stat().st_mode & 0o777 == 0o600
               for name in ('restic', 'rclone'))


def test_state_limit_and_link_refusal(tmp_path, monkeypatch):
    (tmp_path / 'safe').write_bytes(b'12345')
    monkeypatch.setattr(probe, 'STATE_LIMIT', 4)
    with pytest.raises(core.BundleError):
        probe._state_size(tmp_path)
    monkeypatch.setattr(probe, 'STATE_LIMIT', 100)
    (tmp_path / 'link').symlink_to(tmp_path / 'safe')
    with pytest.raises(core.BundleError):
        probe._state_size(tmp_path)


def test_controller_failure_does_not_return_raw_diagnostics(staged, monkeypatch, capsys):
    inputs, result, digest = staged
    class Executor:
        def call(self, fn, values, timeout):
            assert 0 < timeout <= 300 and time.monotonic() < values[-1] <= time.monotonic() + 270
            raise RuntimeError('SYNTHETIC-private')
    assert probe.main(['--tools', result['directory'], '--receipt-sha256', result['receipt_sha256'],
        '--pins', str(inputs['path']), '--pins-sha256', digest, '--execute'], executor=Executor()) == 1
    assert 'SYNTHETIC-private' not in capsys.readouterr().out


@pytest.mark.parametrize('code', [0, 1, 2, 10, 11, 130, True])
def test_unrelated_error_is_not_wrong_key_proof(code):
    assert probe._wrong_key_rejected(code) is False


def test_specific_wrong_key_exit_and_corrupt_pack_summary_required():
    assert probe._wrong_key_rejected(12) is True
    pack = 'a' * 64
    raw = core._encode({'message_type': 'summary', 'num_errors': 1, 'broken_packs': [pack]})
    assert probe._corruption_rejected(1, raw, pack) is True
    assert probe._corruption_rejected(11, raw, pack) is False
    assert probe._corruption_rejected(1, b'generic transport failure', pack) is False
    assert probe._corruption_rejected(1, raw, 'b' * 64) is False


@pytest.mark.parametrize('elapsed', [9.0, 301.0])
def test_parent_preparation_consumes_the_same_attempt_budget(staged, tmp_path, monkeypatch, capsys, elapsed):
    inputs, result, digest = staged
    now = [0.0]
    calls = []
    monkeypatch.setattr(probe.time, 'monotonic', lambda: now[0])
    monkeypatch.setattr(probe, 'verify_tools', lambda *args, **kwargs: ({}, {}))
    def create_parent(**kwargs):
        parent = tmp_path / 'bounded-probe'
        parent.mkdir(mode=0o700)
        now[0] = elapsed
        return str(parent)
    monkeypatch.setattr(probe.tempfile, 'mkdtemp', create_parent)
    class Executor:
        def call(self, fn, values, timeout):
            calls.append((values, timeout))
            return {'status': 'INCOMPLETE', 'offsite_verified': False}
    assert probe.main(['--tools', result['directory'], '--receipt-sha256', result['receipt_sha256'],
        '--pins', str(inputs['path']), '--pins-sha256', digest, '--execute'], executor=Executor()) == 1
    if elapsed > 300:
        assert calls == []
    else:
        assert len(calls) == 1 and calls[0][1] <= 300 - elapsed
        assert calls[0][0][-1] <= 270
