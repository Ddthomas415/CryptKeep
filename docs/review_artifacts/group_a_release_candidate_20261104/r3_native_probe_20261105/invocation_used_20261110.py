"""One owner-approved image acquisition and disposable R3 fixture operation."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from datetime import datetime, timezone

ROOT = Path('/Users/baitus/Downloads/crypto-bot-pro/docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105')
CLI = Path('/Applications/Docker.app/Contents/Resources/bin/docker')
CLI_SHA = 'e6bb967adc3e97c9a9027aa7a1b83691789630cb26a4bbcddd2e8353a8a89ea4'
PACKET_SHA = '9027d7ddcdca0b45c639c64156af15c32418cf221fdde890049a34434d84f95c'
HUB = 'https://hub.docker.com/v2/repositories/library/python/tags/3.12-slim'
LABEL = 'com.cryptkeep.r3-attempt'
EXPECTED = dict(scope='synthetic_linux_processes_only', tests=7, failures=0, errors=0, skips=0)

class Stop(Exception):
    pass

def need(condition, reason):
    if not condition:
        raise Stop(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def unpack(target):
    raw = (ROOT / 'group_a_linux_probe.tar.gz').read_bytes()
    need(sha(raw) == PACKET_SHA, 'packet_digest_changed')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        members = archive.getmembers()
        need(len(members) == len({m.name for m in members}) == 22, 'packet_members_changed')
        need(all(m.isfile() and m.size <= 262144 and not m.name.startswith('/') and
                 '..' not in PurePosixPath(m.name).parts and
                 re.fullmatch(r'[A-Za-z0-9_./]+', m.name) for m in members), 'unsafe_packet')
        data = {m.name: archive.extractfile(m).read() for m in members}
    manifest = json.loads(data['MANIFEST.json'])
    need(manifest['schema'] == 1 and len(manifest['files']) == 21 and
         set(data) == set(manifest['files']) | {'MANIFEST.json'}, 'manifest_scope_changed')
    need(sum(map(len, data.values())) <= 524288, 'packet_too_large')
    for name, spec in manifest['files'].items():
        need(name.endswith('.py') and len(data[name]) == spec['bytes'] and
             sha(data[name]) == spec['sha256'], 'member_digest_changed')
    target.mkdir(mode=0o755)
    for name, raw in data.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o755)
        with path.open('xb') as handle:
            handle.write(raw)
        path.chmod(0o644)

def capture(argv, env, cwd, seconds, cap):
    end = time.monotonic() + seconds
    raw = bytearray()
    failure = None
    with subprocess.Popen(argv, env=env, cwd=cwd, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
        with selectors.DefaultSelector() as select:
            select.register(proc.stdout, selectors.EVENT_READ)
            while True:
                remaining = end - time.monotonic()
                if remaining <= 0 or not select.select(remaining):
                    failure = 'timeout'
                    break
                part = os.read(proc.stdout.fileno(), min(4096, cap + 1 - len(raw)))
                if not part:
                    break
                raw.extend(part)
                if len(raw) > cap:
                    failure = 'output_limit'
                    break
        if failure:
            proc.kill()
        try:
            proc.wait(timeout=max(.05, end - time.monotonic()))
        except subprocess.TimeoutExpired:
            failure = failure or 'timeout'
            proc.kill()
    return dict(exit=proc.returncode, failure=failure, output=bytes(raw[:cap]).decode('utf8', 'replace'))

def okay(result, stage):
    need(result['exit'] == 0 and result['failure'] is None,
         stage + ':' + (result['failure'] or 'command_failed'))
    return result['output'].strip()

def platform_digest(data):
    need(data.get('name') == '3.12-slim' and isinstance(data.get('images'), list), 'unexpected_hub_tag')
    matches = {image['digest'] for image in data['images'] if
               image.get('architecture') == 'arm64' and image.get('os') == 'linux' and
               image.get('variant') in ('v8', '', None)}
    need(len(matches) == 1, 'ambiguous_arm64_manifest')
    value = next(iter(matches))
    need(re.fullmatch(r'sha256:[0-9a-f]{64}', value), 'invalid_manifest_digest')
    return value

def main():
    need(sys.argv[1:] in (['--smoke'], ['--run']), 'explicit_mode_required')
    with tempfile.TemporaryDirectory(prefix='cbp-r3-pull-', dir='/private/tmp') as tmp:
        base = Path(tmp)
        payload = base / 'source'
        unpack(payload)
        config = base / 'config'
        config.mkdir(mode=0o700)
        env = {'PATH': '/usr/bin:/bin', 'HOME': tmp, 'LC_ALL': 'C'}
        if sys.argv[1:] == ['--smoke']:
            need(capture(['/usr/bin/printf', '%s\n', 'argument-proof'], env, tmp, 3, 1024) ==
                 dict(exit=0, failure=None, output='argument-proof\n'), 'argument_smoke_failed')
            need(capture(['/usr/bin/printf', '%s\n', 'overflow'], env, tmp, 3, 4)['failure'] ==
                 'output_limit', 'output_smoke_failed')
            need(platform_digest({'name': '3.12-slim', 'images': [
                {'os': 'linux', 'architecture': 'arm64', 'variant': 'v8', 'digest': 'sha256:' + 'a'*64}
            ]}) == 'sha256:' + 'a'*64, 'manifest_smoke_failed')
            print('SMOKE passed: packet, child argv/output, cap, arm64 digest; zero Docker calls')
            return 0
        token = uuid.uuid4().hex
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        receipt = ROOT / f'pull_test_{stamp}_{token[:8]}.jsonl'
        print(f'RECEIPT {receipt}', flush=True)
        with receipt.open('x', encoding='utf8') as log:
            def emit(kind, **data):
                log.write(json.dumps(dict(kind=kind, **data), sort_keys=True) + '\n')
                log.flush()
                os.fsync(log.fileno())
            emit('authorization', owner='Approve one image pull and test', cli_sha256=CLI_SHA,
                 packet_sha256=PACKET_SHA, image_source=HUB, utc=stamp, scope='synthetic_linux_processes_only')
            docker = [str(CLI), '--config', str(config), '--host',
                      'unix:///Users/baitus/.docker/run/docker.sock']
            stage = 'local_inputs'
            owned = None
            create_attempted = False
            pull_attempted = False
            removed = None
            failure = None
            fixtures = None
            test_end = None
            count = 0
            command_bytes = 0
            started = time.monotonic()
            cidfile = base / 'cid'
            def run(name, args, timeout=10, cap=2048, cleanup=False, is_docker=True):
                nonlocal count, command_bytes
                available = (65536 if cleanup else 57344) - command_bytes
                need(available > 0, 'aggregate_output_budget_exhausted')
                if test_end is not None:
                    timeout = min(timeout, test_end - (0 if cleanup else 40) - time.monotonic())
                need(timeout > 0, name + ':no_time_budget')
                argv = docker + args if is_docker else args
                count += int(is_docker)
                result = capture(argv, env, tmp, timeout, min(cap, available))
                command_bytes += len(result['output'].encode('utf8'))
                emit('command', stage=name, argv=argv, **result)
                return result
            def state():
                fmt = ('{"id":{{json .Id}},"label":{{json (index .Config.Labels "com.cryptkeep.r3-attempt")}},'
                       '"running":{{json .State.Running}},"status":{{json .State.Status}},"exit":{{json .State.ExitCode}}}')
                data = json.loads(okay(run('owned_state', ['container', 'inspect', '--format', fmt, owned],
                                          cleanup=True), 'owned_state'))
                need(data['id'] == owned and data['label'] == token and type(data['running']) is bool,
                     'container_ownership_unconfirmed')
                return data
            try:
                need(not CLI.is_symlink() and sha(CLI.read_bytes()) == CLI_SHA, 'cli_digest_changed')
                stage = 'daemon'
                fmt = '{"os":{{json .Server.Os}},"arch":{{json .Server.Arch}},"api":{{json .Server.APIVersion}}}'
                daemon = json.loads(okay(run(stage, ['version', '--format', fmt]), stage))
                need(daemon['os'] == 'linux' and daemon['arch'] == 'arm64', 'daemon_platform_changed')
                stage = 'official_tag_metadata'
                raw = okay(run(stage, ['/usr/bin/curl', '--disable', '--fail', '--silent', '--show-error',
                    '--proto', '=https', '--max-redirs', '0', '--max-time', '15', HUB],
                    timeout=15, cap=32768, is_docker=False), stage)
                pinned = platform_digest(json.loads(raw))
                ref = 'docker.io/library/python@' + pinned
                emit('pinned_image', reference=ref, platform='linux/arm64', source=HUB,
                     response_sha256=sha(raw.encode('utf8')))
                stage = 'one_image_pull'
                pull_attempted = True
                okay(run(stage, ['image', 'pull', '--platform', 'linux/arm64', ref],
                         timeout=180, cap=8192), stage)
                test_end = time.monotonic() + 180
                stage = 'image_identity'
                fmt = '{"id":{{json .Id}},"digests":{{json .RepoDigests}},"os":{{json .Os}},"arch":{{json .Architecture}}}'
                image = json.loads(okay(run(stage, ['image', 'inspect', '--format', fmt, ref], cap=4096), stage))
                need(re.fullmatch('sha256:[0-9a-f]{64}', image['id']) and image['os'] == 'linux' and
                     image['arch'] == 'arm64' and any(value in image['digests'] for value in
                     (ref, 'python@'+pinned, 'docker.io/library/python@'+pinned)), 'image_identity_not_pinned')
                emit('validated_image', **image)
                need(sha(CLI.read_bytes()) == CLI_SHA, 'cli_digest_changed_before_create')
                need(test_end - time.monotonic() >= 140, 'insufficient_test_budget')
                stage = 'one_container_create'
                create_attempted = True
                created = run(stage, ['container', 'create', '--name', 'cbp-r3-'+token,
                    '--label', LABEL+'='+token, '--cidfile', str(cidfile), '--pull=never',
                    '--network=none', '--read-only', '--user=65534:65534', '--cap-drop=ALL',
                    '--security-opt=no-new-privileges', '--pids-limit=32', '--memory=256m',
                    '--cpus=1', '--init', '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,mode=1777,size=64m',
                    '--mount', f'type=bind,source={payload},target=/probe,readonly',
                    '--entrypoint', '/usr/local/bin/python3', image['id'], '-I', '-S', '-B',
                    '/probe/scripts/research/verify_group_a_linux_processes.py', '--run-linux-fixtures'])
                saved = cidfile.read_text().strip() if cidfile.is_file() else ''
                printed = created['output'].strip()
                if re.fullmatch('[0-9a-f]{64}', saved) and (not re.fullmatch('[0-9a-f]{64}', printed) or saved == printed):
                    owned = saved
                elif not saved and re.fullmatch('[0-9a-f]{64}', printed):
                    owned = printed
                need(owned is not None, 'container_creation_identity_unconfirmed')
                emit('owned_container', id=owned, label=token)
                okay(created, stage)
                stage = 'native_fixtures'
                output = okay(run(stage, ['container', 'start', '--attach', owned], timeout=90, cap=16384), stage)
                fixtures = json.loads(output.splitlines()[-1])
                need(fixtures == EXPECTED, 'seven_clean_fixture_passes_not_observed')
            except Exception as error:
                failure = str(error) if isinstance(error, Stop) else type(error).__name__
                emit('stop', stage=stage, reason=failure)
            finally:
                if owned:
                    try:
                        current = state()
                        if current['running']:
                            okay(run('owned_stop', ['container', 'stop', '--timeout', '3', owned], cleanup=True), 'owned_stop')
                            current = state()
                        need(not current['running'] and current['status'] in ('created', 'exited', 'dead'),
                             'container_stopped_state_unconfirmed')
                        if fixtures == EXPECTED and (current['status'] != 'exited' or current['exit'] != 0):
                            failure = failure or 'container_exit_not_zero'
                        need(okay(run('owned_remove', ['container', 'rm', owned], cleanup=True), 'owned_remove') == owned,
                             'owned_removal_response_unconfirmed')
                        removed = True
                    except Exception as error:
                        removed = False
                        emit('cleanup_unconfirmed', id=owned,
                             reason=str(error) if isinstance(error, Stop) else type(error).__name__)
                elif create_attempted:
                    removed = False
            passed = failure is None and fixtures == EXPECTED and removed is True
            result = dict(status='seven_fixtures_passed' if passed else 'INCOMPLETE', failure=failure,
                          stage=stage, fixture=fixtures, pull_attempted=pull_attempted,
                          creation_attempted=create_attempted, container_id=owned,
                          owned_removal_confirmed=removed, docker_calls=count,
                          elapsed_seconds=round(time.monotonic()-started, 3))
            emit('result', **result)
            print(json.dumps(result, sort_keys=True), flush=True)
            return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
