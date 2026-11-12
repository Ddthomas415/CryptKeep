"""Read-only supplemental metadata. Constants are supplied by a reviewed renderer."""
import json
import os
from pathlib import Path
import pwd
import signal
import stat
import subprocess
import time
from types import SimpleNamespace
from datetime import datetime, timezone


def arm_deadline(deadline):
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        raise TimeoutError('capture_budget_exhausted')
    signal.setitimer(signal.ITIMER_REAL, remaining)


def inspect_compatibility():
    deadline = time.monotonic() + 70
    arm_deadline(deadline)
    captured = []
    namespace = {'__name__': 'prior_readonly_inventory',
                 'print': lambda raw: captured.append(json.loads(raw))}
    exec(compile(PRIOR_SOURCE, 'reviewed_prior_inventory', 'exec'), namespace)
    # The old collector's reset/cancel calls cannot extend this capture's deadline.
    namespace['signal'] = SimpleNamespace(alarm=lambda _seconds: arm_deadline(deadline))
    if namespace['inspect']() != 0 or len(captured) != 1:
        return 2
    base = captured[0]
    if base.get('checkout_head', {}).get('output', '').strip() != EXPECTED_BASE:
        return 3
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        return 4
    # The prior collector cancels its alarm on completion; restore the shared remainder.
    arm_deadline(deadline)
    env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'HOME': '/nonexistent',
           'SYSTEMD_PAGER': 'cat', 'SYSTEMD_COLORS': '0'}
    def command(argv, cap=16384):
        remaining = min(5, deadline-time.monotonic())
        if remaining <= 0:
            return {'status': 'budget_exhausted'}
        try:
            run = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL,
                                 capture_output=True, timeout=remaining)
            return {'exit': run.returncode, 'output': run.stdout[:cap].decode('utf8', 'replace'),
                    'truncated': len(run.stdout) > cap or len(run.stderr) > 1024}
        except Exception:
            return {'status': 'unavailable'}
    manager = command(['/usr/bin/systemctl', '--version'], 2048)
    packages = command(['/srv/cryptkeep/app/.venv/bin/python', '-I', '-S', '-B', '-c',
        '''import json,sys,os,stat
from pathlib import Path
site=Path('/srv/cryptkeep/app/.venv/lib/python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'/site-packages')
result={}
for name in ('ccxt','pyyaml','numpy','pytest'):
    if site.resolve()!=site or not site.is_dir():
        result[name]={'status':'unavailable'};continue
    found=[p for p in site.glob('*.dist-info') if p.name.lower().startswith(name+'-')]
    if len(found)!=1:
        result[name]={'status':'absent_at_inspected_site' if not found else 'ambiguous'}
        continue
    metadata=found[0]/'METADATA'
    if found[0].is_symlink() or metadata.resolve().parent!=found[0] or not metadata.resolve().is_relative_to(site):
        result[name]={'status':'unavailable'};continue
    try:
        with os.fdopen(os.open(metadata,os.O_RDONLY|os.O_NOFOLLOW),'rb') as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size>1048576:
                result[name]={'status':'unavailable'};continue
            raw=stream.read(65536).decode('utf8','replace')
    except OSError:
        result[name]={'status':'unavailable'};continue
    values=[line.removeprefix('Version: ').strip() for line in raw.splitlines() if line.startswith('Version: ')]
    result[name]={'version':values[0]} if len(values)==1 else {'status':'unavailable'}
print(json.dumps({'site':str(site),'packages':result}))'''])
    proposed = command(['/usr/bin/systemctl', 'show', '--no-pager',
                        '--property=Id,LoadState,ActiveState', '--', *PROFILE['units']])
    paths = []
    for name in PROFILE['paths']:
        row = {'path': name}
        try:
            meta = Path(name).lstat()
            row.update(present=True, uid=meta.st_uid, gid=meta.st_gid,
                       mode=oct(meta.st_mode & 0o7777), directory=stat.S_ISDIR(meta.st_mode),
                       symlink=stat.S_ISLNK(meta.st_mode))
            if stat.S_ISDIR(meta.st_mode):
                capacity = os.statvfs(name)
                row.update(available_bytes=capacity.f_bavail*capacity.f_frsize,
                           available_inodes=capacity.f_favail)
        except FileNotFoundError:
            row['present'] = False
        except OSError:
            row['status'] = 'unavailable'
        paths.append(row)
    users = {}
    for name in PROFILE['users']:
        try:
            user = pwd.getpwnam(name)
            users[name] = {'present': True, 'uid': user.pw_uid, 'gid': user.pw_gid}
        except KeyError:
            users[name] = {'present': False}
        except OSError:
            users[name] = {'status': 'unavailable'}
    output = {'base': base, 'compatibility': {
        'candidate_sha256': PROFILE['candidate_sha256'], 'release': PROFILE['release'],
        'manager': manager, 'package_metadata': packages, 'proposed_units': proposed,
        'candidate_paths': paths, 'proposed_users': users,
        'finished_utc': datetime.now(timezone.utc).isoformat()}}
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(inspect_compatibility())
