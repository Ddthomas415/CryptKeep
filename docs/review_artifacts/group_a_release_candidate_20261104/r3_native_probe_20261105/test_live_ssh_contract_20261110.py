"""Offline regression checks: ssh -G evaluates options without a connection."""
import importlib.util
import os
from pathlib import Path
import subprocess

import pytest

PATH = Path(__file__).with_name('live_ssh_contract_20261110.py')
SPEC = importlib.util.spec_from_file_location('local_live_ssh_contract', PATH)
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)

def effective(argv):
    result = subprocess.run(argv, env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'},
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=5, check=True)
    fields = {}
    for line in result.stdout.decode().splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            fields[parts[0]] = parts[1]
    return fields

def test_old_actual_effective_options_reject_short_packet_deadline():
    old = [value.replace('ServerAliveInterval=0', 'ServerAliveInterval=5')
           .replace('ServerAliveCountMax=3', 'ServerAliveCountMax=1')
           for value in CONTRACT.configuration_argv()]
    fields = effective(old)
    assert fields['connecttimeout'] == '210'
    assert fields['serveraliveinterval'] == '5'
    with pytest.raises(ValueError, match='packet_timeout_shorter'):
        CONTRACT.validate_effective(fields)

def test_corrected_actual_effective_options_and_outer_bound():
    fields = effective(CONTRACT.configuration_argv())
    CONTRACT.validate_effective(fields)
    argv = CONTRACT.live_argv()
    assert argv[:4] == ['/usr/bin/perl', '-e', 'alarm 300; exec @ARGV or die "exec failed: $!";', '--']
    assert argv[4:] == [CONTRACT.SSH, *CONTRACT.OPTIONS, CONTRACT.TARGET, 'python3 -I -S -B -']

@pytest.mark.parametrize('key,value', [('stricthostkeychecking', 'false'),
    ('connectionattempts', '2'), ('forwardagent', 'yes'), ('connecttimeout', '0'),
    ('hostname', 'other-host')])
def test_reject_changed_scope_or_security(key, value):
    fields = {'hostname': '100.86.128.9', 'user': 'cryptkeep', 'connecttimeout': '210',
              'serveraliveinterval': '0', 'serveralivecountmax': '3',
              'connectionattempts': '1', 'stricthostkeychecking': 'true',
              'updatehostkeys': 'false', 'forwardagent': 'no', 'batchmode': 'yes',
              'controlmaster': 'false', 'loglevel': 'VERBOSE'}
    fields[key] = value
    with pytest.raises(ValueError):
        CONTRACT.validate_effective(fields)
