"""Read-only in-memory SSH command; not a deployment or application startup."""
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import signal
import sqlite3
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone

def inspect():
    expected = 'ubuntu-4gb-nbg1-3'
    user = pwd.getpwuid(os.geteuid()).pw_name
    hostname = platform.node()
    if hostname != expected or user != 'cryptkeep':
        print(json.dumps({'status': 'identity_mismatch', 'hostname': hostname, 'user': user}))
        return 2
    deadline = time.monotonic() + 70
    signal.alarm(70)
    env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'HOME': '/nonexistent',
           'GIT_OPTIONAL_LOCKS': '0', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'SYSTEMD_PAGER': 'cat', 'SYSTEMD_COLORS': '0'}
    def command(args, cap=16384):
        remaining = min(5, deadline-time.monotonic())
        if remaining <= 0:
            return {'status': 'budget_exhausted'}
        try:
            run = subprocess.run(args, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=remaining)
            return {'exit': run.returncode, 'output': run.stdout[:cap].decode('utf8', 'replace'),
                    'error': run.stderr[:1024].decode('utf8', 'replace'),
                    'truncated': len(run.stdout)>cap or len(run.stderr)>1024}
        except Exception as exc:
            return {'status': type(exc).__name__}
    out = {'status': 'observed', 'utc': datetime.now(timezone.utc).isoformat(),
           'hostname': hostname, 'user': user, 'uid': os.geteuid(),
           'os': platform.system(), 'release': platform.release(), 'architecture': platform.machine(),
           'system_python': sys.version, 'system_sqlite': sqlite3.sqlite_version}
    root = Path('/srv/cryptkeep/app')
    out['checkout_head'] = command(['/usr/bin/git', '-C', str(root), 'rev-parse', 'HEAD'])
    venv = root / '.venv/bin/python'
    if venv.is_file():
        code = 'import json,sys,sqlite3; print(json.dumps({"python":sys.version,"sqlite":sqlite3.sqlite_version,"executable":sys.executable}))'
        out['checkout_runtime'] = command([str(venv), '-I', '-S', '-B', '-c', code])
    else:
        out['checkout_runtime'] = {'status': 'missing_interpreter'}
    sources = ('services/alerts/group_a_supervisor.py', 'services/alerts/group_a_summary_delivery.py',
               'services/alerts/group_a_summary_protocol.py', 'services/alerts/group_a_summary_transport.py',
               'services/control/group_a_systemd_policy.py', 'services/control/group_a_account_units.py',
               'services/execution/paper_engine.py', 'services/execution/strategy_runner.py',
               'services/market_data/paper_snapshot_quote.py', 'services/market_data/system_status_publisher.py',
               'scripts/run_group_a_alert.py')
    out['sources'] = {}
    for name in sources:
        path = root / name
        try:
            meta = path.lstat()
            if not stat.S_ISREG(meta.st_mode) or meta.st_size>1048576 or not path.resolve().is_relative_to(root.resolve()):
                out['sources'][name] = {'status': 'not_approved_regular_source'}
            else:
                out['sources'][name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': meta.st_size}
        except FileNotFoundError:
            out['sources'][name] = {'status': 'missing'}
        except Exception as exc:
            out['sources'][name] = {'status': type(exc).__name__}
    listed = command(['/usr/bin/systemctl', 'list-unit-files', '--no-legend', '--no-pager'], cap=32768)
    group_a = []
    if listed.get('exit') == 0 and not listed.get('truncated'):
        for line in listed['output'].splitlines():
            name = line.split()[0] if line.split() else ''
            if name.startswith('cbp-group-a-') and name.endswith(('.service', '.target', '.timer')):
                group_a.append(name)
    out['unit_inventory'] = {'exit': listed.get('exit'), 'error': listed.get('error'),
                             'truncated': listed.get('truncated'), 'group_a_names': group_a[:64],
                             'group_a_count': len(group_a)}
    fields = ('Id', 'LoadState', 'ActiveState', 'SubState', 'FragmentPath', 'User', 'Group', 'Restart',
              'NoNewPrivileges', 'ProtectSystem', 'ReadWritePaths', 'ReadOnlyPaths', 'StateDirectory',
              'UMask', 'WorkingDirectory', 'OnFailure', 'PartOf', 'ConditionResult')
    selected = group_a[:24] + ['cbp-crypto-edge-collector.service', 'cbp-edge-cadence.service']
    if selected:
        out['selected_unit_properties'] = command(
            ['/usr/bin/systemctl', 'show', '--no-pager', '--property='+','.join(fields)] + selected,
            cap=16384)
    out['paths'] = []
    for name in ('/srv/cryptkeep', '/srv/cryptkeep/app', '/srv/cryptkeep/releases', '/srv/cryptkeep/state',
                 '/var/lib/cryptkeep', '/run/cryptkeep', '/etc/systemd/system'):
        path = Path(name)
        value = {'path': name}
        try:
            meta = path.lstat()
            value.update(present=True, mode=oct(meta.st_mode & 0o7777), uid=meta.st_uid, gid=meta.st_gid,
                         directory=stat.S_ISDIR(meta.st_mode), symlink=stat.S_ISLNK(meta.st_mode))
            if stat.S_ISDIR(meta.st_mode):
                capacity = os.statvfs(path)
                value.update(available_bytes=capacity.f_bavail*capacity.f_frsize,
                             available_inodes=capacity.f_favail)
        except FileNotFoundError:
            value['present'] = False
        except Exception as exc:
            value['error'] = type(exc).__name__
        out['paths'].append(value)
    try:
        memory = {}
        for line in Path('/proc/meminfo').read_text().splitlines():
            key, _, raw = line.partition(':')
            if key in ('MemTotal', 'MemAvailable'):
                memory[key+'_bytes'] = int(raw.split()[0])*1024
        out['memory'] = memory
    except Exception as exc:
        out['memory'] = {'status': type(exc).__name__}
    signal.alarm(0)
    print(json.dumps(out, sort_keys=True))
    return 0

if __name__ == '__main__':
    sys.exit(inspect())
