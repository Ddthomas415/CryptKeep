"""Synthetic input and ssh -G only; no connection, token or account access."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

PATH = Path(__file__).with_name('ssh_stage_diagnostics_20261111.py')
SPEC = importlib.util.spec_from_file_location('stage_diagnostics', PATH)
D = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D)


def test_saved_failure_yields_check_not_approval_or_cause():
    d = D.StageFilter()
    out = d.feed(D.CHECK + b'\n# To authenticate, visit: https://login.tailscale.com/a/synthetic\n')
    assert out == [('stage', 'ssh_check_requested'), ('approval_url', 'https://login.tailscale.com/a/synthetic')]
    receipt = json.dumps(d.receipt())
    assert 'synthetic' not in receipt and 'https://' not in receipt
    assert d.receipt()['observed_client_markers'] == ['ssh_check_requested']
    assert d.receipt()['causal_diagnosis'] == 'UNVERIFIED'


def test_fragmentation_crlf_dedup_and_unterminated_line():
    d = D.StageFilter()
    blob = b'debug1: Connection established.\r\n' * 2 + D.CHECK + b'\n'
    out = []
    for value in blob:
        out.extend(d.feed(bytes([value])))
    assert out == [('stage', 'transport_connected'), ('stage', 'ssh_check_requested')]
    d.feed(b'debug1: Sending command: python3 -I -S -B -')
    d.finish()
    assert 'remote_command_requested' not in d.receipt()['observed_client_markers']


@pytest.mark.parametrize('line', [
    b'# To authenticate, visit: https://login.tailscale.com.evil/a/secret',
    b'# To authenticate, visit: https://login.tailscale.com/a/secret?token=secret',
    b'# To authenticate, visit: https://login.tailscale.com/a/secret\x1b[0m',
    b'Authenticated to other-host ([100.86.128.9]:22) using "none".',
    b'debug1: Connection established. password=secret',
    b'debug1: Offering public key: /Users/secret/.ssh/id secret',
    b'Authorization: Bearer secret',
])
def test_unknown_secret_or_wrong_identity_lines_do_not_escape(line):
    d = D.StageFilter()
    assert d.feed(line + b'\n') == []
    assert 'secret' not in json.dumps(d.receipt())


def test_link_requires_check_and_only_first_link_is_emitted():
    d = D.StageFilter()
    link = b'# To authenticate, visit: https://login.tailscale.com/a/synthetic\n'
    assert d.feed(link) == []
    d.feed(D.CHECK + b'\n')
    assert len(d.feed(link)) == 1
    assert d.feed(link) == []


def test_oversized_line_discarded_and_next_line_recovers():
    d = D.StageFilter()
    for _ in range(100):
        assert d.feed(b'secret' * 1000) == []
        assert len(d._pending) <= D.MAX_LINE
    assert d.feed(b'\n' + D.CHECK + b'\n') == [('stage', 'ssh_check_requested')]


def test_independent_markers_are_not_promoted_to_inventory_success():
    d = D.StageFilter()
    out = d.feed(b'Authenticated to 100.86.128.9 ([100.86.128.9]:22) using "none".\n'
                 b'debug1: Sending command: python3 -I -S -B -\n'
                 b'debug1: Exit status 0\n')
    assert len(out) == 3
    assert d.receipt()['remote_inventory_validated'] is False


def effective(argv):
    result = subprocess.run(['/usr/bin/ssh', '-G', *argv[5:-2], argv[-2]],
                            stdin=subprocess.DEVNULL, capture_output=True, timeout=5, check=True,
                            env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    return dict(line.split(None, 1) for line in result.stdout.decode().splitlines() if ' ' in line)


def test_argv_preserves_existing_contract_except_debug_level():
    argv = D.diagnostic_argv()
    assert argv[:4] == ['/usr/bin/perl', '-e', 'alarm 300; exec @ARGV or die "exec failed: $!";', '--']
    assert argv[-2:] == ['cryptkeep@100.86.128.9', 'python3 -I -S -B -']
    assert argv.count('LogLevel=DEBUG1') == 1
    D.validate_diagnostic(argv, effective(argv))


@pytest.mark.parametrize('change', ['LogLevel=VERBOSE', 'ForwardAgent=yes', 'ConnectionAttempts=2'])
def test_exact_argv_and_actual_loglevel_drift_rejected(change):
    argv = D.diagnostic_argv()
    fields = effective(argv)
    altered = argv + ['-v']
    with pytest.raises(ValueError, match='argv_changed'):
        D.validate_diagnostic(altered, fields)
    if change == 'LogLevel=VERBOSE':
        fields['loglevel'] = 'VERBOSE'
        with pytest.raises(ValueError, match='loglevel_changed'):
            D.validate_diagnostic(argv, fields)
    else:
        before = change.split('=')[0] + ('=no' if change.startswith('Forward') else '=1')
        altered = [change if item == before else item for item in argv]
        with pytest.raises(ValueError, match='argv_changed'):
            D.validate_diagnostic(altered, fields)


def test_cli_defaults_to_secret_free_stages_only():
    run = subprocess.run([sys.executable, '-B', str(PATH)],
                         input=D.CHECK + b'\n# To authenticate, visit: https://login.tailscale.com/a/synthetic\nBearer secret\n',
                         capture_output=True, timeout=5, check=True)
    assert run.stdout == b'SSH_STAGE ssh_check_requested\n'
    assert run.stderr == b''


def test_marker_order_and_receipt_copy_are_preserved():
    d = D.StageFilter()
    d.feed(D.CHECK + b'\ndebug1: Connection established.\n')
    receipt = d.receipt()
    assert receipt['observed_client_markers'] == ['ssh_check_requested', 'transport_connected']
    receipt['observed_client_markers'].append('invented')
    assert 'invented' not in d.receipt()['observed_client_markers']


@pytest.mark.parametrize('name,error', [
    ('live_ssh_contract_20261110.py', 'contract_hash_changed'),
    ('host_preflight_command_20261110.py', 'command_hash_changed'),
])
def test_changed_reviewed_inputs_fail_closed(tmp_path, monkeypatch, name, error):
    for filename in ('live_ssh_contract_20261110.py', 'host_preflight_command_20261110.py'):
        data = (D.ROOT / filename).read_bytes()
        (tmp_path / filename).write_bytes(data + (b'\n' if filename == name else b''))
    monkeypatch.setattr(D, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match=error):
        D.diagnostic_argv()


def test_explicit_url_handoff_is_not_receipt_safe_output():
    run = subprocess.run([sys.executable, '-B', str(PATH), '--show-owner-approval-url'],
                         input=D.CHECK + b'\n# To authenticate, visit: https://login.tailscale.com/a/synthetic\n',
                         capture_output=True, timeout=5, check=True)
    assert run.stdout == (b'SSH_STAGE ssh_check_requested\n'
                          b'SSH_APPROVAL_URL https://login.tailscale.com/a/synthetic\n')
    assert run.stderr == b''
