"""Real local Python subprocesses only; never opens an SSH connection."""
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

PATH = Path(__file__).with_name('instrumented_ssh_preflight_20261111.py')
SPEC = importlib.util.spec_from_file_location('instrumented_preflight', PATH)
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)


def fixture_inventory():
    return {'status': 'observed', 'utc': '2026-11-11T11:00:00Z',
            'hostname': 'ubuntu-4gb-nbg1-3', 'user': 'cryptkeep', 'uid': 1000,
            'os': 'Linux', 'architecture': 'aarch64', 'release': '6.8.0',
            'system_python': '3.12.3 (compiler details)', 'system_sqlite': '3.45.1',
            'checkout_head': {'exit': 0, 'truncated': False, 'output': 'a'*40+'\n', 'error': ''},
            'sources': {name: {'status': 'missing'} for name in W.SOURCE_NAMES},
            'checkout_runtime': {'status': 'missing_interpreter'},
            'unit_inventory': {'group_a_count': 0, 'group_a_names': []},
            'paths': [], 'memory': {}}


def collect(tmp_path, code, *, stdin=b'', emit=None, duration=.6, state=None):
    state = {} if state is None else state
    stage = W._load_stage()
    with (tmp_path/'synthetic_receipt.json').open('w+b') as handle:
        raw = W._collect([sys.executable, '-I', '-S', '-B', '-c', code], stdin,
                         stage['StageFilter'](), handle, state,
                         emit=emit or (lambda kind, value: None),
                         work_seconds=duration, cleanup_seconds=.5)
    return state, raw


def test_prepare_uses_actual_ssh_G_but_never_connects():
    argv, command, reducer = W.prepare()
    assert argv[-2:] == ['cryptkeep@100.86.128.9', 'python3 -I -S -B -']
    assert 'LogLevel=DEBUG1' in argv
    assert W.hashlib.sha256(command).hexdigest() == W._load_stage()['COMMAND_SHA']
    assert reducer.receipt()['remote_inventory_validated'] is False


def test_default_cli_and_API_never_call_prepare_or_launch(monkeypatch):
    monkeypatch.setattr(W, 'prepare', lambda: pytest.fail('prepare must not run'))
    assert W.run_once(None)['connection_processes_started'] == 0
    run = subprocess.run([sys.executable, '-B', str(PATH)], capture_output=True, timeout=5)
    assert run.returncode == 1
    assert json.loads(run.stdout)['outcome'] == 'not_executed'
    assert run.stderr == b''


def test_inventory_projection_does_not_retain_arbitrary_text():
    value = fixture_inventory()
    value['checkout_runtime']['error'] = 'Bearer secret-from-remote'
    result = W.inventory_summary(json.dumps(value).encode())
    assert result['system_python'] == '3.12.3'
    assert result['checkout_head'] == 'a'*40
    assert result['full_inventory_retained'] is False
    assert 'secret-from-remote' not in json.dumps(result)


@pytest.mark.parametrize('raw', [
    b'{"status":"observed","status":"observed"}',
    b'{"status":NaN}', b'{"status":Infinity}', b'{} trailing',
    b'\xff', b'['*1100, b'Bearer secret', b'{}'*2,
])
def test_invalid_inventory_never_echoes_input(raw):
    with pytest.raises(W.Refused) as error:
        W.inventory_summary(raw)
    assert 'secret' not in str(error.value)


@pytest.mark.parametrize('field,value', [('hostname', 'other-host'), ('user', 'root'),
    ('architecture', 'unknown'), ('uid', True), ('system_python', 'secret'), ('extra', 'secret')])
def test_identity_schema_and_metadata_fail_closed(field, value):
    inventory = fixture_inventory()
    inventory[field] = value
    with pytest.raises(W.Refused):
        W.inventory_summary(json.dumps(inventory).encode())


def test_one_process_filters_before_receipt_and_binds_URL_to_saved_pid(tmp_path):
    events = []
    lines = ('debug1: Connection established.\n# Tailscale SSH requires an additional check.\n'
             '# To authenticate, visit: https://login.tailscale.com/a/synthetic\nBearer secret\n')
    code = 'import sys,time; sys.stderr.write('+repr(lines)+'); sys.stderr.flush(); time.sleep(.2); print("{}")'
    def emit(kind, value):
        saved = json.loads((tmp_path/'synthetic_receipt.json').read_bytes())
        assert saved['owned_pid'] > 0 and saved['connection_processes_started'] == 1
        os.kill(saved['owned_pid'], 0)
        events.append((kind, value))
    state, raw = collect(tmp_path, code, emit=emit)
    assert state['outcome'] == 'stdout_received'
    assert raw == b'{}\n'
    assert ('approval_url', 'https://login.tailscale.com/a/synthetic') in events
    assert state['connection_processes_started'] == 1
    assert state['owned_leader_reaped'] is True
    durable = (tmp_path/'synthetic_receipt.json').read_text() + json.dumps(state)
    assert 'https://' not in durable and 'secret' not in durable


def test_blocked_stdin_respects_deadline_and_reaps_owned_leader(tmp_path):
    start = time.monotonic()
    state, _ = collect(tmp_path, 'import time; time.sleep(10)', stdin=b'x'*1048576, duration=.15)
    assert state['outcome'] == 'work_deadline'
    assert state['owned_leader_reaped'] is True
    assert time.monotonic()-start < 2


@pytest.mark.parametrize('stream,reason', [('stdout', 'stdout_limit'), ('stderr', 'stderr_limit')])
def test_output_flood_is_bounded_and_owned_child_cleaned(tmp_path, stream, reason):
    state, raw = collect(tmp_path, 'import sys,time; sys.'+stream+'.write("x"*200000); sys.'+stream+'.flush(); time.sleep(10)')
    assert state['outcome'] == reason
    assert len(raw) <= W.CAP
    assert state['owned_leader_reaped'] is True


def test_leader_exit_does_not_strand_descendant_holding_pipes(tmp_path):
    tick = tmp_path/'descendant_tick'
    child = ('import time; from pathlib import Path; p=Path('+repr(str(tick))+'); '
             '[(p.write_text(str(i)),time.sleep(.03)) for i in range(300)]')
    parent = ('import subprocess,sys; subprocess.Popen([sys.executable,"-I","-S","-B","-c",'
              +repr(child)+']); print("{}")')
    state, _ = collect(tmp_path, parent, duration=.3)
    assert state['outcome'] == 'work_deadline'
    assert state['owned_leader_reaped'] is True
    before = tick.read_text()
    time.sleep(.12)
    assert tick.read_text() == before
    assert state['descendant_reaping_verified'] is False


@pytest.mark.parametrize('error', [OSError('secret'), KeyboardInterrupt()])
def test_handoff_failure_or_interrupt_cleans_up_without_echo(tmp_path, error):
    def emit(*_):
        raise error
    code = 'import sys,time; sys.stderr.write("debug1: Connection established.\\n"); sys.stderr.flush(); time.sleep(10)'
    state, _ = collect(tmp_path, code, emit=emit)
    assert state['owned_leader_reaped'] is True
    assert state['outcome'] in {'controller_failure', 'operator_interrupt'}
    assert 'secret' not in json.dumps(state)


def test_receipt_failure_after_spawn_still_cleans_up(tmp_path, monkeypatch):
    monkeypatch.setattr(W, '_save', lambda *_: (_ for _ in ()).throw(OSError('secret')))
    state, _ = collect(tmp_path, 'import time; time.sleep(10)')
    assert state['outcome'] == 'controller_failure'
    assert state['owned_leader_reaped'] is True
    assert 'secret' not in json.dumps(state)


def test_no_link_after_leader_exit(tmp_path):
    events = []
    child = ('import sys,time; time.sleep(.15); sys.stderr.write('
             '"# Tailscale SSH requires an additional check.\\n# To authenticate, visit: https://login.tailscale.com/a/stale\\n"); sys.stderr.flush()')
    parent = 'import subprocess,sys; subprocess.Popen([sys.executable,"-I","-S","-B","-c",'+repr(child)+'])'
    state, _ = collect(tmp_path, parent, emit=lambda *event: events.append(event))
    assert all(kind != 'approval_url' for kind, _ in events)
    assert state['owned_leader_reaped'] is True


def test_receipt_collision_never_launches_and_existing_bytes_preserved(tmp_path, monkeypatch):
    receipt = tmp_path/'instrumented_attempt_fixture.json'
    receipt.write_bytes(b'preserve')
    monkeypatch.setattr(W, 'ROOT', tmp_path)
    monkeypatch.setattr(W, 'prepare', lambda: ([], b'', None))
    monkeypatch.setattr(W.subprocess, 'Popen', lambda *_a, **_k: pytest.fail('must not launch'))
    with pytest.raises(FileExistsError):
        W.run_once(receipt, execute=True)
    assert receipt.read_bytes() == b'preserve'


def test_full_synthetic_integration_is_single_attempt_and_private_receipt(tmp_path, monkeypatch):
    stage = W._load_stage()
    code = 'print('+repr(json.dumps(fixture_inventory()))+')'
    argv = [sys.executable, '-I', '-S', '-B', '-c', code]
    monkeypatch.setattr(W, 'ROOT', tmp_path)
    monkeypatch.setattr(W, 'prepare', lambda: (argv, b'', stage['StageFilter']()))
    monkeypatch.setattr(W, '_terminal_emit', lambda *_: lambda *_: None)
    receipt = tmp_path/'instrumented_attempt_fixture.json'
    result = W.run_once(receipt, execute=True)
    assert result['outcome'] == 'identity_bound_partial_inventory_received'
    assert result['status'] == 'INCOMPLETE'
    assert result['connection_processes_started'] == 1 and result['automatic_retry'] is False
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    assert json.loads(receipt.read_bytes()) == result


def test_group_signals_precede_reap_and_poll_never_used(tmp_path, monkeypatch):
    original_popen = W.subprocess.Popen
    original_kill = W._kill_group
    signals = []
    class NoPoll(original_popen):
        def poll(self):
            pytest.fail('poll reaps and breaks the PID fence')
        def wait(self, *args, **kwargs):
            assert self.pid in signals
            return super().wait(*args, **kwargs)
    def checked_kill(pid):
        signals.append(pid)
        return original_kill(pid)
    def guarded_popen(argv, *args, **kwargs):
        cls = original_popen if argv[0] == '/bin/ps' else NoPoll
        return cls(argv, *args, **kwargs)
    monkeypatch.setattr(W.subprocess, 'Popen', guarded_popen)
    monkeypatch.setattr(W, '_kill_group', checked_kill)
    state, _ = collect(tmp_path, 'print(123)')
    assert state['outcome'] == 'stdout_received'
    assert signals == [state['owned_pid']]
    assert state['owned_leader_reaped'] is True


@pytest.mark.parametrize('stdout,code,expected', [
    (b'12345 12345 Z\n', 0, True), (b'12345 12345 S\n', 0, False),
    (b'12345 99999 Z\n', 0, False), (b'99999 12345 Z\n', 0, False),
    (b'12345 12345 Z\n', 1, False), (b'', 0, False), (b'secret', 0, False),
])
def test_permission_denial_needs_matching_zombie_only_group_evidence(monkeypatch, stdout, code, expected):
    owned = W._OwnedChild.__new__(W._OwnedChild)
    owned.process = SimpleNamespace(pid=12345)
    owned.finish_by = time.monotonic()+1
    monkeypatch.setattr(W.subprocess, 'run', lambda *_a, **_k: SimpleNamespace(returncode=code, stdout=stdout))
    assert owned._zombies_only() is expected


def test_closed_signalling_fence_cannot_target_reused_pid():
    owned = W._OwnedChild.__new__(W._OwnedChild)
    owned.lock = W.threading.Lock()
    owned.signalling_open = False
    assert owned.kill() == 'signalling_closed'


def test_valid_json_with_nonzero_exit_is_not_success(tmp_path):
    code = 'import sys; print('+repr(json.dumps(fixture_inventory()))+'); sys.exit(7)'
    state, _ = collect(tmp_path, code)
    assert state['outcome'] == 'connection_exit_nonzero'
    assert state['exit_code'] == 7


def test_early_stdin_close_is_not_success(tmp_path):
    state, _ = collect(tmp_path, 'import os,time; os.close(0); time.sleep(.05); print(123)',
                       stdin=b'x'*1048576)
    assert state['outcome'] == 'stdin_closed_early'
    assert state['owned_leader_reaped'] is True


def test_cleanup_uncertainty_cannot_be_promoted_to_inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(W, '_kill_group', lambda *_: 'kill_unconfirmed')
    monkeypatch.setattr(W._OwnedChild, '_zombies_only', lambda *_: False)
    state, _ = collect(tmp_path, 'print(123)')
    assert state['outcome'] == 'cleanup_unconfirmed'
    assert state['owned_leader_reaped'] is True


@pytest.mark.parametrize('with_descendant', [False, True])
def test_first_SIGINT_during_cleanup_is_deferred_and_handler_restored(tmp_path, monkeypatch, with_descendant):
    original_popen = W.subprocess.Popen
    original_kill = W._kill_group
    original_handler = W.signal.getsignal(W.signal.SIGINT)
    children = []
    interrupted = []
    tick = tmp_path/'closed_stdio_descendant_tick'
    def track(*args, **kwargs):
        child = original_popen(*args, **kwargs)
        if kwargs.get('start_new_session'):
            children.append(child)
        return child
    def interrupt_first_kill(pid):
        if not interrupted:
            interrupted.append(True)
            os.kill(os.getpid(), W.signal.SIGINT)
        return original_kill(pid)
    monkeypatch.setattr(W.subprocess, 'Popen', track)
    monkeypatch.setattr(W, '_kill_group', interrupt_first_kill)
    code = 'print(123)'
    if with_descendant:
        descendant = ('import time; from pathlib import Path; p=Path('+repr(str(tick))+'); '
                      '[(p.write_text(str(i)),time.sleep(.02)) for i in range(300)]')
        code = ('import subprocess,sys,time; from pathlib import Path; '
                'subprocess.Popen([sys.executable,"-I","-S","-B","-c",'+repr(descendant)+'], '
                'stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); '
                'p=Path('+repr(str(tick))+'); '
                'exec("while not p.exists(): time.sleep(.01)"); print(123)')
    escaped = False
    state = {}
    try:
        state, _ = collect(tmp_path, code, state=state)
    except KeyboardInterrupt:
        escaped = True
    finally:
        # Regression must also clean its fixture when run against the broken source.
        for child in children:
            if child.returncode is None:
                original_kill(child.pid)
                child.wait(timeout=1)
    assert not escaped
    assert interrupted == [True]
    assert state['outcome'] == 'operator_interrupt'
    assert state['owned_leader_reaped'] is True
    assert W.signal.getsignal(W.signal.SIGINT) == original_handler
    if with_descendant:
        before = tick.read_text()
        time.sleep(.1)
        assert tick.read_text() == before
