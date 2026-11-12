"""Bounded synthetic checks of an existing local composed candidate only."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]


def run(destination, failed_from=None):
    destination = Path(destination).resolve()
    manifest = json.loads((destination/'MANIFEST.json').read_bytes())
    original = json.loads((destination/'TREE_MANIFEST.json').read_bytes())
    tree = Path(manifest['scratch_tree'])
    if not tree.is_relative_to('/private/tmp') or not tree.name == 'tree':
        raise ValueError('unexpected_scratch_tree')
    for name, entry in original.items():
        if hashlib.sha256((tree/name).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('composed_tree_drift')
    scratch = tree.parent
    prefix = 'focused_' if failed_from is not None else ''
    for name in ('state', 'home', 'tmp'):
        (scratch/(prefix+name)).mkdir()
    env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'HOME': str(scratch/(prefix+'home')),
        'CBP_STATE_DIR': str(scratch/(prefix+'state')), 'TMPDIR': str(scratch/(prefix+'tmp')),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
        'PYTHONPATH': str(tree), 'CBP_R5_BEFORE_RUNNER': str(tree/manifest['r5_before_fixture'])}
    program = '''import socket,sys
def refused(*args, **kwargs):
    raise OSError("network_disabled_for_candidate_rehearsal")
socket.socket.connect = refused
socket.socket.connect_ex = refused
socket.getaddrinfo = refused
socket.gethostbyname = refused
socket.gethostbyname_ex = refused
import pytest
sys.exit(pytest.main(sys.argv[1:]))
'''
    selected = manifest['test_files']
    if failed_from is not None:
        selected = [case.get('classname').replace('.', '/')+'.py::'+case.get('name')
                    for case in ET.parse(failed_from).getroot().iter('testcase')
                    if case.find('failure') is not None or case.find('error') is not None]
        if not selected or any(node.split('::')[0] not in manifest['test_files'] for node in selected):
            raise ValueError('failed_selection_outside_frozen_scope')
    args = [str(ROOT/'.venv/bin/python'), '-B', '-c', program, '-q', '-p', 'no:cacheprovider',
            '--tb=short', '-ra', '--junitxml='+str(destination/(prefix+'pytest.xml')), *selected]
    receipt = {'status': 'INCOMPLETE', 'scope': 'local_synthetic_candidate_only',
               'test_files': selected, 'scratch_tree': str(tree),
               'linux_dependency_lock': None, 'host_actions': False,
               'network_guard': 'parent_test_interpreter_only_not_kernel_isolation',
               'main_test_seconds_limit': 300, 'automatic_retry': False}
    path = destination/(prefix+'TEST_RESULT.json')
    with path.open('x') as claim:
        json.dump(receipt, claim)
    started = time.monotonic()
    interrupted = [False]
    def defer(_signum, _frame):
        interrupted[0] = True
    prior = signal.signal(signal.SIGINT, defer)
    process = None
    try:
        with (destination/(prefix+'pytest_output.txt')).open('x') as output:
            process = subprocess.Popen(args, cwd=tree, env=env, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
            receipt['owned_test_pid'] = process.pid
            while True:
                remaining = 300-(time.monotonic()-started)
                if interrupted[0] or remaining <= 0:
                    receipt['outcome'] = 'interrupted' if interrupted[0] else 'test_deadline'
                    # wait timeout has not reaped this owned session leader.
                    os.killpg(process.pid, signal.SIGKILL)
                    receipt['exit_code'] = process.wait(timeout=10)
                    break
                try:
                    receipt['exit_code'] = process.wait(timeout=min(.5, remaining))
                    receipt['outcome'] = 'tests_exited'
                    break
                except subprocess.TimeoutExpired:
                    continue
    finally:
        try:
            if process is not None and process.returncode is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                receipt['exit_code'] = process.wait(timeout=10)
            receipt['elapsed_seconds'] = round(time.monotonic()-started, 3)
            receipt['source_mutations'] = [name for name, entry in original.items()
                if not (tree/name).is_file() or hashlib.sha256((tree/name).read_bytes()).hexdigest() != entry['sha256']]
            path.write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
        finally:
            signal.signal(signal.SIGINT, prior)
    return receipt


if __name__ == '__main__':
    result = run(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
    print(json.dumps({key: result.get(key) for key in
        ('status', 'outcome', 'exit_code', 'elapsed_seconds', 'source_mutations')}))
