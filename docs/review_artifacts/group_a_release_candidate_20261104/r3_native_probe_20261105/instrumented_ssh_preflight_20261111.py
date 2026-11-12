"""One-shot preflight integration. No network activity without explicit opt-in."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import selectors
import signal
import stat
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
STAGE_SHA = '6bee6d9ab67668557fa638d8a2b2bf74cf97ff8816b2be3f419640eb187284b9'
CAP = 131072
ENV = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}
SOURCE_NAMES = (
    'services/alerts/group_a_supervisor.py', 'services/alerts/group_a_summary_delivery.py',
    'services/alerts/group_a_summary_protocol.py', 'services/alerts/group_a_summary_transport.py',
    'services/control/group_a_systemd_policy.py', 'services/control/group_a_account_units.py',
    'services/execution/paper_engine.py', 'services/execution/strategy_runner.py',
    'services/market_data/paper_snapshot_quote.py', 'services/market_data/system_status_publisher.py',
    'scripts/run_group_a_alert.py',
)


class Refused(Exception):
    """Only fixed internal reason codes may be passed to this exception."""


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _load_stage():
    path = ROOT / 'ssh_stage_diagnostics_20261111.py'
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != STAGE_SHA:
        raise Refused('stage_hash_changed')
    namespace = {'__file__': str(path), '__name__': 'reviewed_stage_module'}
    exec(compile(source, str(path), 'exec'), namespace)
    return namespace


def prepare():
    """Hash-bound source and local ssh -G only; never opens a connection."""
    stage = _load_stage()
    command = (ROOT / 'host_preflight_command_20261110.py').read_bytes()
    if hashlib.sha256(command).hexdigest() != stage['COMMAND_SHA']:
        raise Refused('command_hash_changed')
    argv = stage['diagnostic_argv']()
    probe = subprocess.run(['/usr/bin/ssh', '-G', *argv[5:-2], argv[-2]],
                           env=ENV, stdin=subprocess.DEVNULL, capture_output=True,
                           timeout=5, check=True)
    fields = dict(line.split(None, 1) for line in probe.stdout.decode().splitlines() if ' ' in line)
    stage['validate_diagnostic'](argv, fields)
    return argv, command, stage['StageFilter']()


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise Refused('inventory_duplicate_key')
        value[key] = item
    return value


def _json(raw):
    def nonfinite(_):
        raise Refused('inventory_nonfinite')
    return json.loads(raw, object_pairs_hook=_pairs, parse_constant=nonfinite)


def _version(raw):
    if type(raw) is not str:
        raise Refused('inventory_version_invalid')
    match = re.match(r'\A([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})(?:\s|$)', raw)
    if not match:
        raise Refused('inventory_version_invalid')
    return match.group(1)


def inventory_summary(raw):
    """Persist a conservative metadata projection, never arbitrary remote text."""
    if len(raw) > CAP:
        raise Refused('stdout_limit')
    try:
        value = _json(raw)
        allowed = {'status', 'utc', 'hostname', 'user', 'uid', 'os', 'release',
                   'architecture', 'system_python', 'system_sqlite', 'checkout_head',
                   'checkout_runtime', 'sources', 'unit_inventory', 'selected_unit_properties',
                   'paths', 'memory'}
        if type(value) is not dict or not set(value) <= allowed:
            raise Refused('inventory_schema_invalid')
        if (value.get('status') != 'observed' or value.get('hostname') != 'ubuntu-4gb-nbg1-3'
                or value.get('user') != 'cryptkeep'):
            raise Refused('inventory_identity_unconfirmed')
        if value.get('os') != 'Linux' or value.get('architecture') not in {'aarch64', 'x86_64', 'arm64'}:
            raise Refused('inventory_platform_invalid')
        if type(value.get('uid')) is not int or not 0 <= value['uid'] < 2**32:
            raise Refused('inventory_uid_invalid')
        stamp = datetime.fromisoformat(value['utc'])
        if stamp.utcoffset() is None:
            raise Refused('inventory_time_invalid')
        summary = {key: value[key] for key in ('hostname', 'user', 'uid', 'os', 'architecture')}
        summary.update(utc=stamp.astimezone(timezone.utc).isoformat(),
                       system_python=_version(value['system_python']),
                       system_sqlite=_version(value['system_sqlite']))
        sources = value['sources']
        if type(sources) is not dict or set(sources) != set(SOURCE_NAMES):
            raise Refused('inventory_sources_invalid')
        summary['sources'] = {}
        for name, entry in sources.items():
            if (type(entry) is dict and set(entry) == {'sha256', 'bytes'}
                    and type(entry['sha256']) is str and re.fullmatch('[a-f0-9]{64}', entry['sha256'])
                    and type(entry['bytes']) is int and 0 <= entry['bytes'] <= 1048576):
                summary['sources'][name] = entry
            elif type(entry) is dict and set(entry) == {'status'} and entry['status'] in {
                    'missing', 'not_approved_regular_source', 'PermissionError', 'OSError'}:
                summary['sources'][name] = entry
            else:
                raise Refused('inventory_sources_invalid')
        head = value['checkout_head']
        if type(head) is not dict:
            raise Refused('inventory_head_invalid')
        if head.get('exit') == 0 and head.get('truncated') is False:
            if type(head.get('output')) is not str or not re.fullmatch('[a-f0-9]{40}\n?', head['output']):
                raise Refused('inventory_head_invalid')
            summary['checkout_head'] = head['output'].strip()
        else:
            summary['checkout_head'] = 'unavailable'
        # Unrestricted command/error strings and unit-policy values are not retained.
        # This is intentionally a partial inventory, not host compatibility acceptance.
        for key in ('checkout_runtime', 'unit_inventory', 'selected_unit_properties', 'paths', 'memory', 'release'):
            if key in value:
                encoded = json.dumps(value[key], sort_keys=True, allow_nan=False).encode()
                summary[key + '_sha256_not_values'] = hashlib.sha256(encoded).hexdigest()
        summary['full_inventory_retained'] = False
        return summary
    except Refused:
        raise
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        raise Refused('inventory_invalid') from None


def _save(handle, state):
    payload = json.dumps(state, sort_keys=True, allow_nan=False).encode() + b'\n'
    handle.seek(0)
    handle.write(payload)
    handle.truncate()
    handle.flush()
    os.fsync(handle.fileno())


def _kill_group(pid):
    try:
        os.killpg(pid, signal.SIGKILL)
        return 'kill_sent'
    except ProcessLookupError:
        return 'already_absent'
    except OSError:
        return 'kill_unconfirmed'


class _OwnedChild:
    """Retain the unreaped leader as a PID/PGID fence until signalling is disabled."""

    def __init__(self, process, finish_by):
        self.process = process
        self.finish_by = finish_by
        self.lock = threading.Lock()
        self.signalling_open = True
        self.kill_sent = False
        self.queue = None
        self.dead = False
        if not hasattr(os, 'waitid'):
            self.queue = select.kqueue()
            event = select.kevent(process.pid, filter=select.KQ_FILTER_PROC,
                                 flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                 fflags=select.KQ_NOTE_EXIT)
            try:
                self.queue.control([event], 0, 0)
            except ProcessLookupError:
                self.dead = True

    def alive(self):
        # Neither waitid(WNOWAIT) nor kqueue NOTE_EXIT reaps the leader.
        if self.queue is None:
            return os.waitid(os.P_PID, self.process.pid,
                             os.WEXITED | os.WNOHANG | os.WNOWAIT) is None
        if self.queue.control([], 1, 0):
            self.dead = True
        return not self.dead

    def kill(self):
        with self.lock:
            if not self.signalling_open:
                return 'signalling_closed'
            result = _kill_group(self.process.pid)
            if result == 'kill_sent':
                self.kill_sent = True
            elif result == 'kill_unconfirmed' and self.kill_sent:
                # A concurrent watchdog already sent SIGKILL under this fence.
                result = 'kill_sent'
            if result == 'kill_unconfirmed' and not self.alive() and self._zombies_only():
                return 'no_live_members'
            return result

    def _zombies_only(self):
        # Darwin can refuse a signal to a group consisting only of zombies.
        # Do not reinterpret permission denial as success without group evidence.
        remaining = min(1, self.finish_by-time.monotonic())
        if remaining <= 0:
            return False
        try:
            probe = subprocess.run(['/bin/ps', '-o', 'pid=,pgid=,stat=', '-g', str(self.process.pid)],
                                   stdin=subprocess.DEVNULL, capture_output=True, timeout=remaining,
                                   env=ENV)
            if probe.returncode != 0 or len(probe.stdout) > 65536:
                return False
            rows = [line.split() for line in probe.stdout.decode('ascii').splitlines()]
            return (0 < len(rows) <= 1024
                    and any(row[0] == str(self.process.pid) for row in rows if row)
                    and all(len(row) == 3 and row[0].isdigit()
                            and row[1] == str(self.process.pid)
                            and re.fullmatch(r'Z[+A-Za-z<>-]*', row[2]) for row in rows))
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return False

    def close_before_reap(self):
        with self.lock:
            self.signalling_open = False
        if self.queue is not None:
            self.queue.close()


def _collect(argv, command, reducer, handle, state, *, emit, work_seconds=295, cleanup_seconds=5):
    """One owned process. Synthetic tests supply Python children, never SSH."""
    process = None
    owned = None
    watchdog = None
    output = bytearray()
    started = time.monotonic()
    deadline = started + work_seconds
    finish_by = deadline + cleanup_seconds
    state.update(status='INCOMPLETE', outcome='controller_failure', started_utc=_utc())
    interrupted = [False]
    previous_handler = None
    handler_installed = False
    def defer_sigint(_signum, _frame):
        interrupted[0] = True
    try:
        # A first Ctrl-C may arrive in finally itself: defer it from before spawn.
        previous_handler = signal.signal(signal.SIGINT, defer_sigint)
        handler_installed = True
        if not hasattr(os, 'waitid') and not hasattr(select, 'kqueue'):
            raise Refused('nonreaping_child_watch_unavailable')
        process = subprocess.Popen(argv, env=ENV, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True,
                                   close_fds=True, bufsize=0)
        owned = _OwnedChild(process, finish_by)
        watchdog = threading.Timer(max(0, deadline-time.monotonic()), owned.kill)
        watchdog.daemon = True
        watchdog.start()
        state.update(owned_pid=process.pid, connection_processes_started=1)
        _save(handle, state)  # Must precede any possible owner-link disclosure.
        offset = 0
        stderr_bytes = 0
        with selectors.DefaultSelector() as selector:
            for pipe, label in ((process.stdin, 'stdin'), (process.stdout, 'stdout'), (process.stderr, 'stderr')):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_WRITE if label == 'stdin' else selectors.EVENT_READ, label)
            while selector.get_map():
                if interrupted[0]:
                    raise Refused('operator_interrupt')
                if time.monotonic() >= deadline:
                    raise Refused('work_deadline')
                for key, _ in selector.select(min(.05, max(0, deadline-time.monotonic()))):
                    if interrupted[0]:
                        raise Refused('operator_interrupt')
                    if time.monotonic() >= deadline:
                        raise Refused('work_deadline')
                    try:
                        if key.data == 'stdin':
                            offset += os.write(key.fd, command[offset:offset+4096]) if offset < len(command) else 0
                            if offset == len(command):
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                            continue
                        chunk = os.read(key.fd, 4096)
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        raise Refused('stdin_closed_early') from None
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if key.data == 'stdout':
                        if len(output) + len(chunk) > CAP:
                            raise Refused('stdout_limit')
                        output.extend(chunk)
                    else:
                        stderr_bytes += len(chunk)
                        if stderr_bytes > CAP:
                            raise Refused('stderr_limit')
                        for kind, value in reducer.feed(chunk):
                            if interrupted[0]:
                                raise Refused('operator_interrupt')
                            if time.monotonic() >= deadline:
                                raise Refused('work_deadline')
                            if kind == 'stage':
                                state['diagnostics'] = reducer.receipt()
                                _save(handle, state)
                                emit(kind, value)
                            elif owned.alive() and time.monotonic() < deadline:
                                emit(kind, value)
            while owned.alive():
                if interrupted[0]:
                    raise Refused('operator_interrupt')
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    raise Refused('work_deadline')
                time.sleep(min(.01, remaining))
            if offset != len(command):
                raise Refused('stdin_incomplete')
            state.update(outcome='stdout_received')
    except Refused as exc:
        state['outcome'] = str(exc)
    except KeyboardInterrupt:
        state['outcome'] = 'operator_interrupt'
    except subprocess.TimeoutExpired:
        state['outcome'] = 'work_deadline'
    except Exception:
        state['outcome'] = 'controller_failure'
    finally:
        try:
            if process is not None:
                if watchdog is not None:
                    watchdog.cancel()
                state['owned_group_cleanup'] = owned.kill() if owned is not None else _kill_group(process.pid)
                if owned is not None:
                    owned.close_before_reap()
                try:
                    state['exit_code'] = process.wait(timeout=max(0, finish_by-time.monotonic()))
                    state['owned_leader_reaped'] = True
                except (subprocess.TimeoutExpired, OSError):
                    state['owned_leader_reaped'] = False
                for pipe in (process.stdin, process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
            if watchdog is not None:
                watchdog.join(timeout=max(0, min(.1, finish_by-time.monotonic())))
            reducer.finish()
            state.update(diagnostics=reducer.receipt(), finished_utc=_utc(),
                         elapsed_seconds=round(time.monotonic()-started, 3),
                         descendant_reaping_verified=False, automatic_retry=False)
            state['work_outcome'] = state['outcome']
            if state.get('owned_leader_reaped') is False or state.get('owned_group_cleanup') == 'kill_unconfirmed':
                state['outcome'] = 'cleanup_unconfirmed'
            elif interrupted[0]:
                state['outcome'] = 'operator_interrupt'
            elif state['outcome'] == 'stdout_received' and state.get('exit_code') != 0:
                state['outcome'] = 'connection_exit_nonzero'
            state['sigint_requested'] = interrupted[0]
        finally:
            if handler_installed:
                signal.signal(signal.SIGINT, previous_handler)
    return bytes(output)


def _terminal_emit(show_url):
    def emit(kind, value):
        if kind == 'approval_url' and not show_url:
            return
        prefix = 'SSH_STAGE ' if kind == 'stage' else 'SSH_APPROVAL_URL '
        data = (prefix + value + '\n').encode('ascii')
        # Never let a non-draining terminal extend the owned process lifetime.
        fd = sys.stdout.fileno()
        previous = os.get_blocking(fd)
        try:
            os.set_blocking(fd, False)
            if os.write(fd, data) != len(data):
                raise Refused('handoff_output_unavailable')
        except (OSError, BlockingIOError):
            raise Refused('handoff_output_unavailable') from None
        finally:
            os.set_blocking(fd, previous)
    return emit


def run_once(receipt, *, execute=False, show_url=False):
    if execute is not True:
        return {'status': 'INCOMPLETE', 'outcome': 'not_executed', 'connection_processes_started': 0}
    # CLI receipts are new regular files in this existing approved artifact folder.
    receipt = Path(receipt)
    if receipt.parent.resolve() != ROOT or not re.fullmatch(r'instrumented_attempt_[A-Za-z0-9_-]{1,80}\.json', receipt.name):
        raise Refused('receipt_path_refused')
    argv, command, reducer = prepare()
    fd = os.open(receipt, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w+b') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise Refused('receipt_not_regular')
        state = {'schema': 1, 'status': 'INCOMPLETE', 'outcome': 'prepared',
                 'bot_relation': 'BOT_RULES', 'runtime_trading_configuration_checked': False,
                 'connection_processes_started': 0, 'stage_sha256': STAGE_SHA,
                 'remote_command_sha256': hashlib.sha256(command).hexdigest(),
                 'owner_url_display_enabled': show_url is True}
        _save(handle, state)
        raw = _collect(argv, command, reducer, handle, state, emit=_terminal_emit(show_url))
        if state['outcome'] == 'stdout_received':
            try:
                state['inventory_summary'] = inventory_summary(raw)
                state['outcome'] = 'identity_bound_partial_inventory_received'
            except Refused as exc:
                state['outcome'] = str(exc)
        _save(handle, state)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-read-only-preflight', action='store_true')
    parser.add_argument('--show-owner-approval-url', action='store_true')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    try:
        result = run_once(args.receipt, execute=args.execute_read_only_preflight,
                          show_url=args.show_owner_approval_url)
        print(json.dumps({key: result[key] for key in ('status', 'outcome', 'connection_processes_started')}))
    except Exception:
        print('{"status":"INCOMPLETE","outcome":"preflight_refused"}')
        return 1
    return 0 if result['outcome'] == 'identity_bound_partial_inventory_received' else 1


if __name__ == '__main__':
    sys.exit(main())
