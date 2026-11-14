"""Synthetic sandbox refusals only; no subprocess or native-client execution."""
import errno
import json
import time

import pytest

from scripts.research import probe_group_a_backup_native as probe
from services.control import group_a_backup_bundle as core
from tests.test_group_a_backup_native_policy import staged
from tests.test_group_a_backup_tools import inputs as tool_inputs


PRIVATE = b'SYNTHETIC-PRIVATE-key-password-/private/not-for-output\x1b[31m'


@pytest.mark.parametrize('case,phase,reason,exit_code', [
    ('positive_nonzero', 'sandbox_positive', 'native_sandbox_unavailable', 77),
    ('positive_wrong_stdout', 'sandbox_positive', 'native_sandbox_unavailable', 0),
    ('file_unproved', 'sandbox_file_denial', 'native_sandbox_file_denial_unproved', 0),
    ('network_unproved', 'sandbox_network_denial', 'native_sandbox_network_denial_unproved', 7),
    ('file_timeout', 'sandbox_file_denial', 'native_stage_deadline', None),
    ('network_os_error', 'sandbox_network_denial', 'os_error', None),
    ('positive_unknown', 'sandbox_positive', 'unclassified_sandbox_failure', None),
    ('positive_private_bundle_error', 'sandbox_positive', 'unclassified_sandbox_failure', None),
    ('positive_size_limit', 'sandbox_positive', 'native_diagnostic_size_limit', None),
])
def test_worker_returns_safe_current_canary_diagnostics(
        staged, tmp_path, monkeypatch, case, phase, reason, exit_code):
    inputs, result, digest = staged
    parent = tmp_path / 'diagnostic-attempt'
    parent.mkdir(mode=0o700)
    fail_index = {'sandbox_positive': 1, 'sandbox_file_denial': 2,
                  'sandbox_network_denial': 3}[phase]
    calls = []

    def forbidden(*args, **kwargs):
        pytest.fail('diagnostic test must not start a subprocess or build a fixture')

    def command(argv, *args):
        calls.append(argv)
        if len(calls) < fail_index:
            if len(calls) == 1:
                return 0, b'CRYPTKEEP_SYNTHETIC_CANARY\n', b''
            return 1, b'', b'Permission denied'
        assert len(calls) == fail_index
        if case == 'file_timeout':
            raise core.BundleError('native_stage_deadline')
        if case == 'network_os_error':
            raise OSError(errno.EACCES, PRIVATE.decode())
        if case == 'positive_unknown':
            raise RuntimeError(PRIVATE.decode())
        if case == 'positive_private_bundle_error':
            raise core.BundleError(PRIVATE.decode())
        if case == 'positive_size_limit':
            raise core.BundleError('native_diagnostic_size_limit')
        return exit_code, PRIVATE, b'sandbox-exec: sandbox_apply: Operation not permitted\n' + PRIVATE

    monkeypatch.setattr(probe.subprocess, 'Popen', forbidden)
    monkeypatch.setattr(probe, '_command', command)
    monkeypatch.setattr(probe, '_fixture', forbidden)
    output = probe._worker(result['directory'], result['receipt_sha256'],
                           str(inputs['path']), digest, str(parent), time.monotonic() + 10)
    assert output['status'] == 'INCOMPLETE' and output['offsite_verified'] is False
    assert output['phase'] == phase and len(calls) == fail_index
    diagnostic = output['diagnostics']
    assert diagnostic['reason'] == reason
    assert diagnostic['errno'] == (errno.EACCES if case == 'network_os_error' else None)
    if exit_code is None:
        # An exception in a later canary must not reuse the previous canary's result.
        assert diagnostic['command'] is None
    else:
        command_result = diagnostic['command']
        assert command_result['exit_code'] == exit_code
        assert command_result['stdout_bytes'] == len(PRIVATE)
        assert command_result['stderr_markers'] == ['operation_not_permitted', 'sandbox_apply']
        assert command_result['stdout_matches_expected'] is (None if phase == 'sandbox_file_denial' else False)
    encoded = json.dumps(output)
    assert len(encoded) < 1024
    assert 'SYNTHETIC-PRIVATE' not in encoded and str(parent) not in encoded
    assert 'RESTIC_PASSWORD' not in encoded and 'not-for-output' not in encoded


def test_diagnostic_marker_scan_is_bounded_and_never_copies_text():
    error = PRIVATE + b'x' * 4096 + b'Operation not permitted'
    output = probe._sandbox_diagnostics(-9, PRIVATE, error, b'expected')
    assert output == {
        'exit_code': -9, 'stdout_bytes': len(PRIVATE), 'stderr_bytes': len(error),
        'stdout_matches_expected': False, 'stderr_scanned_bytes': 4096,
        'stderr_scan_truncated': True, 'stderr_markers': [],
    }
    assert 'SYNTHETIC-PRIVATE' not in json.dumps(output)


@pytest.mark.parametrize('code', [True, False, 999999, 'SYNTHETIC-PRIVATE'])
def test_invalid_exit_status_is_not_printed_or_treated_as_integer(code):
    output = probe._sandbox_diagnostics(code, b'', b'', b'expected')
    assert output['exit_code'] is None
    assert 'SYNTHETIC-PRIVATE' not in json.dumps(output)
