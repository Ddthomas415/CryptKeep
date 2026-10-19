"""One authorized COPY-only image proof; never install or start services."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tarfile
import tempfile
import time
from datetime import datetime, timezone

ROOT = Path('/Users/baitus/Downloads/crypto-bot-pro')
OUT = ROOT / 'docs/review_artifacts/companion_source_build_20261017'
CLI = Path('/Applications/Docker.app/Contents/Resources/bin/docker')
ENDPOINT = 'unix:///Users/baitus/.docker/run/docker.sock'
CLI_HASH = '31ae2d64e51d9dfc728a2934941615cdd92f31279ed6d5c1fb2bfc0a44637a8f'
BASE = json.loads((ROOT / 'docs/review_artifacts/companion_compatibility_20261016.json').read_text())
FIELDS = {'id': '.Id', 'image': '.Image', 'state': '.State.Status',
          'restarts': '.RestartCount', 'policy': '.HostConfig.RestartPolicy.Name'}
FORMAT = '{' + ','.join(json.dumps(k) + ':{{json ' + v + '}}' for k, v in FIELDS.items()) + '}'
IMAGE_FORMAT = '{"id":{{json .Id}},"layers":{{json .RootFS.Layers}},"onbuild":{{json (index .Config "OnBuild")}}}'
EVENT_FORMAT = '{"time":{{json .TimeNano}},"action":{{json .Action}},"id":{{json .Actor.ID}}}'


def main():
    OUT.mkdir(exist_ok=False)
    report = {'client_date': '2026-10-17', 'status': 'INCOMPLETE', 'commands': [],
              'scope': 'One COPY-only proof image; no installation/startup/query/credentials'}
    deadline = time.monotonic() + 120
    cli_verified = False
    build_verified = False
    with tempfile.TemporaryDirectory(prefix='cki-build-proof-', dir='/private/tmp') as config:
        def save():
            (OUT / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')

        def call(args, payload=None, timeout=10):
            if not cli_verified:
                raise RuntimeError('cli_not_verified')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError('overall_deadline')
            report['commands'].append(list(args))
            save()
            result = subprocess.run([str(CLI), '--config', config, '--host', ENDPOINT, *args],
                                    input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    env={'PATH': '/usr/bin:/bin', 'DOCKER_BUILDKIT': '0'},
                                    timeout=min(timeout, remaining), close_fds=True)
            if result.returncode:
                # Commands contain only fixed public metadata and public source context.
                error = result.stderr.decode(errors='replace')
                report['command_failure'] = {'returncode': result.returncode,
                                            'public_stderr': error[-1500:]}
                raise RuntimeError('docker_command_failed')
            if len(result.stdout) > 2_000_000:
                raise RuntimeError('output_limit')
            return result.stdout

        def inventory():
            return [json.loads(line) for line in call(['container', 'inspect', '--format', FORMAT,
                    *[r['id'] for r in BASE['targets']]]).splitlines()]

        def image(identity):
            return json.loads(call(['image', 'inspect', '--format', IMAGE_FORMAT, identity]))

        try:
            if hashlib.sha256(CLI.read_bytes()).hexdigest() != CLI_HASH:
                raise RuntimeError('cli_identity_changed')
            report['cli_sha256'] = CLI_HASH
            cli_verified = True
            report['before'] = inventory()
            expected = [{'id': r['id'], 'image': r['image_id'], 'state': 'exited',
                         'restarts': 0, 'policy': 'no'} for r in BASE['targets']]
            if report['before'] != expected:
                raise RuntimeError('baseline_changed')
            report['engine_version'] = json.loads(call(['version', '--format', '{{json .Server.Version}}']))
            parent = image(BASE['targets'][3]['image_id'])
            if parent['onbuild'] or not parent['layers']:
                raise RuntimeError('unsafe_parent')
            report['parent'] = parent
            source = ROOT / 'phase1_research_copilot/shared/probe.py'
            if source.is_symlink() or source.resolve() != source:
                raise RuntimeError('source_not_regular')
            with os.fdopen(os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise RuntimeError('source_not_regular')
                raw = stream.read(65537)
            if len(raw) > 65536:
                raise RuntimeError('source_limit')
            if hashlib.sha256(raw).hexdigest() != '9f9251260009a63be1dc02918c5dd70b671e6a4428678ec4f55d75b7923e0228':
                raise RuntimeError('source_identity_changed')
            report['source'] = {'path': str(source.relative_to(ROOT)),
                                'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
            tag = 'cryptkeep-proof-parent:oct17-' + os.urandom(8).hex()
            if tag in call(['image', 'ls', '--format', '{{.Repository}}:{{.Tag}}']).decode().splitlines():
                raise RuntimeError('tag_collision')
            dockerfile = f'FROM {tag}\nCOPY app/shared/probe.py /app/shared/probe.py\n'
            report['dockerfile'] = dockerfile
            context = io.BytesIO()
            with tarfile.open(fileobj=context, mode='w') as archive:
                for name, data in [('Dockerfile', dockerfile.encode()), ('app/shared/probe.py', raw)]:
                    info = tarfile.TarInfo(name)
                    info.size, info.mode, info.mtime = len(data), 0o644, 0
                    archive.addfile(info, io.BytesIO(data))
            payload = context.getvalue()
            (OUT / 'context.tar').write_bytes(payload)
            report['context_sha256'] = hashlib.sha256(payload).hexdigest()
            report['event_start_utc'] = datetime.now(timezone.utc).isoformat()
            call(['image', 'tag', parent['id'], tag])
            report['retained_parent_tag'] = tag
            if image(tag)['id'] != parent['id']:
                raise RuntimeError('parent_tag_changed')
            report['assumption'] = 'No concurrent actor removes or retargets this random parent tag during the single build.'
            report['registry_isolation'] = 'UNVERIFIED; pull=false prefers local, not a hard network prohibition.'
            save()
            report['build_attempts'] = 1
            built_id = call(['build', '--quiet', '--pull=false', '--network=none', '-'], payload, 55).decode().strip()
            if not re.fullmatch(r'sha256:[0-9a-f]{64}', built_id):
                raise RuntimeError('invalid_image_result')
            report['built'] = image(built_id)
            layers = report['built']['layers']
            if layers[:-1] != parent['layers'] or len(layers) != len(parent['layers']) + 1:
                raise RuntimeError('lineage_mismatch')
            report['lineage_verified'] = True
            build_verified = True
        except Exception as exc:
            report['failure'] = type(exc).__name__ + ':' + str(exc)[:100]
        finally:
            try:
                if not cli_verified:
                    raise RuntimeError('cli_unverified_no_final_commands')
                report['after'] = inventory()
                report['originals_unchanged'] = report['after'] == report.get('before')
                if report.get('event_start_utc'):
                    end = datetime.now(timezone.utc).isoformat()
                    report['event_end_utc'] = end
                    report['container_events'] = [json.loads(line) for line in call([
                        'events', '--since', report['event_start_utc'], '--until', end,
                        '--filter', 'type=container', '--format', EVENT_FORMAT]).splitlines()]
                if not report['originals_unchanged'] or report.get('container_events'):
                    report['status'] = 'INCOMPLETE'
                elif build_verified:
                    report['status'] = 'READY_FOR_INDEPENDENT_REVIEW'
            except Exception as exc:
                report['final_check_failure'] = type(exc).__name__ + ':' + str(exc)[:100]
                report['status'] = 'INCOMPLETE'
            save()
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
