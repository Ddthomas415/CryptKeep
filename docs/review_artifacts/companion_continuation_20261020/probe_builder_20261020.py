"""One approved local COPY-only build probe, not installer authorization."""
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import stat
import tarfile
import tempfile
import time
import uuid

from scripts.research import collect_companion_recreation_metadata as capture
from scripts.research import companion_docker_transport as transport
from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CAPTURE = HERE / 'fresh_v5_capture_20261020/capture.json'
CAPTURE_HASH = '0fa450f65997a8ace714babc6b514270eab308cd22f623a6e06177ab3c09fa1b'
OUTPUT = HERE / 'engine_build_probe_20261020'
IMAGE_FORMAT = '{"id":{{json .Id}},"layers":{{json .RootFS.Layers}},"onbuild_present":{{not (not (index .Config "OnBuild"))}}}'
VERSION_FORMAT = '{"version":{{json .Server.Version}},"commit":{{json .Server.GitCommit}}}'


def main():
    raw = CAPTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CAPTURE_HASH:
        raise ValueError('capture_changed_no_commands_run')
    baseline = json.loads(raw)
    if hashlib.sha256(capture.CLI.read_bytes()).hexdigest() != baseline['cli_sha256']:
        raise ValueError('cli_changed_no_commands_run')
    OUTPUT.mkdir(exist_ok=False)  # Fixed consumed probe marker; no automatic retry.
    receipt = core.Receipt(OUTPUT / 'events.jsonl')
    report = {'state': 'INCOMPLETE', 'started_utc': datetime.now(timezone.utc).isoformat(),
              'capture_sha256': CAPTURE_HASH, 'commands': [], 'build_calls': 0,
              'image_retained': None, 'installer_pin_changed': False, 'credentials_accessed': False}
    deadline = time.monotonic() + 60
    lock = None
    old_handler = signal.getsignal(signal.SIGALRM)
    def alarm(*_):
        raise TimeoutError('probe_deadline')
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        lock = os.open('/private/tmp/cryptkeep-companion-install.lock',
                       os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        info = os.fstat(lock)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise ValueError('lock_refused')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tempfile.TemporaryDirectory(prefix='cki-builder-probe-') as config:
            def command(args, label, *, payload=None, build=False, final=False):
                remaining = deadline - (0 if final else 10) - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('probe_budget')
                report['commands'].append(label)
                return transport._run((str(capture.CLI), '--config', config, '--host', capture.ENDPOINT, *args),
                    timeout=min(40 if build else 10, remaining), input_bytes=payload, limit=1_048_576,
                    env={'PATH': '/usr/bin:/bin', 'DOCKER_BUILDKIT': '0'})
            def image(identity, *, final=False):
                row = json.loads(command(('image', 'inspect', '--format', IMAGE_FORMAT, identity),
                                         'public image identity/layers/OnBuild-presence', final=final))
                if (row['id'] != identity or row['onbuild_present'] is not False
                        or type(row['layers']) is not list or len(row['layers']) > 512
                        or any(not install.IMAGE.fullmatch(value) for value in row['layers'])):
                    raise ValueError('image_provenance_refused')
                return row
            def targets(*, final=False):
                identities = [row['id'] for row in baseline['snapshots']]
                result = command(('container', 'inspect', '--format', capture.capture_format(), *identities),
                                 'sanitized seven-target observation', final=final)
                rows = [json.loads(line) for line in result.splitlines()]
                if (len(rows) != 7 or [row.get('id') for row in rows] != identities
                        or [row.get('name', '').removeprefix('/') for row in rows] != list(core.TARGETS)
                        or any(row.get('state') != 'running' or 'flags' not in row for row in rows)):
                    raise ValueError('target_identity_or_state_changed')
                return rows

            engine = json.loads(command(('version', '--format', VERSION_FORMAT), 'engine version/commit'))
            report['engine'] = engine
            if engine != baseline['engine']:
                raise ValueError('engine_changed_since_capture')
            before = targets()
            report['before'] = before
            base = next(row['image'] for row in baseline['snapshots'] if row['name'] == 'phase1-audit-log')
            if next(row['image'] for row in before if row['name'] == '/phase1-audit-log') != base:
                raise ValueError('base_target_changed')
            parent = image(base)
            report['base_image'] = parent
            raw_ids = command(('image', 'ls', '--all', '--no-trunc', '--quiet'), 'existing local image IDs')
            existing = set(raw_ids.decode('ascii').split())
            if not existing or base not in existing or any(not install.IMAGE.fullmatch(value) for value in existing):
                raise ValueError('local_image_inventory_refused')
            nonce = uuid.uuid4().hex
            payload = ('CryptKeep public COPY-only compatibility probe ' + nonce + '\n').encode()
            dockerfile = ('FROM ' + base.removeprefix('sha256:')
                          + '\nCOPY payload.txt /cryptkeep-build-probe/' + nonce + '.txt\n').encode()
            context = io.BytesIO()
            with tarfile.open(fileobj=context, mode='w') as archive:
                for name, value in (('Dockerfile', dockerfile), ('payload.txt', payload)):
                    member = tarfile.TarInfo(name)
                    member.size, member.mode = len(value), 0o644
                    archive.addfile(member, io.BytesIO(value))
            data = context.getvalue()
            (OUTPUT / 'context.tar').write_bytes(data)
            report['context_sha256'] = hashlib.sha256(data).hexdigest()
            report['dockerfile'] = dockerfile.decode('ascii')
            receipt.write({'phase': 'one_build_intended', 'context_sha256': report['context_sha256'],
                           'base_image': base, 'pull': False, 'network': 'none', 'no_run_instructions': True})
            report['build_calls'] = 1
            built = command(('build', '--quiet', '--pull=false', '--network=none', '-'),
                            'single local COPY-only build', payload=data, build=True).decode('ascii').strip()
            if not install.IMAGE.fullmatch(built) or built in existing:
                raise ValueError('new_image_identity_unconfirmed')
            report['image_retained'] = built
            receipt.write({'phase': 'build_acknowledged', 'image': built})
            child = image(built, final=True)
            report['built_image'] = child
            report['parent_layers_preserved'] = child['layers'][:-1] == parent['layers']
            report['exactly_one_copy_layer'] = len(child['layers']) == len(parent['layers']) + 1
            report['after'] = targets(final=True)
            report['seven_targets_unchanged'] = report['after'] == before
            report['engine_after'] = json.loads(command(('version', '--format', VERSION_FORMAT),
                                                       'final engine version/commit', final=True))
            if (report['parent_layers_preserved'] and report['exactly_one_copy_layer']
                    and report['seven_targets_unchanged'] and report['engine_after'] == engine):
                report['state'] = 'READY_FOR_INDEPENDENT_REVIEW'
            receipt.write({'phase': 'probe_checks_complete', 'state': report['state'],
                           'seven_targets_unchanged': report['seven_targets_unchanged']})
    except Exception as error:
        report['failure_category'] = type(error).__name__
        if isinstance(error, core.Refused):
            report['sanitized_detail'] = str(error)
        # Do not retry builds or remove resources after an unknown outcome.
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        if lock is not None:
            os.close(lock)
        receipt.close()
    report['elapsed_seconds'] = round(60 - (deadline - time.monotonic()), 3)
    (OUTPUT / 'report.json').write_bytes(install.canonical(report))
    print(json.dumps({key: report.get(key) for key in ('state', 'engine', 'build_calls', 'image_retained',
        'parent_layers_preserved', 'exactly_one_copy_layer', 'seven_targets_unchanged',
        'elapsed_seconds', 'failure_category', 'sanitized_detail')}))


if __name__ == '__main__':
    main()
