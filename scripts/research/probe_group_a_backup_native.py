"""Prepared local-only native proof. Running downloaded clients needs approval.

No provider transport: the only rclone remote is a private synthetic local
filesystem. Retain owned test files; never reset/unlock an existing repository.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import select
import shutil
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from services.control.group_a_backup_process import OwnedProcessExecutor
from services.control import group_a_backup_bundle as core
from services.control import group_a_backup_prefix as prefix
from services.control import group_a_backup_tools as tools

STATE_LIMIT = 128 << 20
INPUT_LIMIT = 8 << 20


def verify_tools(directory, receipt_sha, pins_path, pins_sha, deadline):
    directory = core._private(directory)
    pins = tools.load_pins(pins_path, pins_sha)
    with core._reader(directory / 'TOOLCHAIN.json') as stream:
        raw = stream.read(16385)
    if len(raw) > 16384 or hashlib.sha256(raw).hexdigest() != core._sha(receipt_sha):
        raise core.BundleError('native_tool_receipt_changed')
    value = core._json(raw)
    if (type(value) is not dict or set(value) != {'format', 'platform', 'pins_sha256', 'tools',
            'clients_executed', 'signature_verified', 'provenance', 'native_execution_authorized'}
            or type(value.get('format')) is not int or value.get('format') != 1 or value.get('platform') != 'darwin_arm64'
            or value.get('pins_sha256') != pins_sha or value.get('clients_executed') is not False
            or value.get('signature_verified') is not False or value.get('native_execution_authorized') is not False
            or value.get('provenance') != 'official_https_api_and_published_checksums'
            or type(value.get('tools')) is not dict or set(value['tools']) != {'restic', 'rclone'}):
        raise core.BundleError('invalid_native_tool_receipt')
    paths = {}
    for name, item in value['tools'].items():
        if (type(item) is not dict or set(item) != {'version', 'archive_sha256', 'binary_sha256', 'binary_bytes', 'relative_path', 'mode'}
                or item.get('version') != pins['tools'][name]['version']
                or item.get('archive_sha256') != pins['tools'][name]['sha256']
                or item.get('relative_path') != 'bin/' + name or item.get('mode') != '0600_NOT_EXECUTABLE'
                or type(item.get('binary_bytes')) is not int or not 0 < item['binary_bytes'] <= tools.MAX_BINARY[name]):
            raise core.BundleError('invalid_native_tool_identity')
        core._sha(item.get('binary_sha256'))
        path = directory / 'bin' / name
        if core._file_hash(path, limit=tools.MAX_BINARY[name], deadline=deadline, clock=time.monotonic) != (
                item['binary_bytes'], item['binary_sha256']):
            raise core.BundleError('native_tool_image_changed')
        paths[name] = path
    return paths, value


def sandbox_profile(parent):
    parent = core._private(parent)
    q = lambda path: json.dumps(str(path))
    executables = [parent / 'bin/restic', parent / 'bin/rclone', Path('/bin/cat'), Path('/usr/bin/python3')]
    runtime = ['/System/Library', '/usr/lib', '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework']
    return '\n'.join([
        '(version 1)', '(deny default)', '(deny network*)', '(allow process-fork)',
        '(allow sysctl-read)', '(allow signal (target self))',
        '(allow process-exec ' + ' '.join('(literal ' + q(p) + ')' for p in executables) + ')',
        '(allow file-read-metadata)',
        '(allow file-read* ' + ' '.join('(subpath ' + q(p) + ')' for p in [parent / 'work', parent / 'bin', *runtime])
            + ' ' + ' '.join('(literal ' + q(p) + ')' for p in ['/bin/cat', '/usr/bin/python3', '/dev/null', '/dev/random', '/dev/urandom']) + ')',
        '(allow file-write* (subpath ' + q(parent / 'work') + ') (literal "/dev/null"))',
    ])


def _state_size(root):
    count = total = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in (*dirs, *files):
            info = (Path(directory) / name).lstat()
            count += 1
            if stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise core.BundleError('unsafe_native_test_state')
            if stat.S_ISREG(info.st_mode):
                total += info.st_size
            if count > 10000 or total > STATE_LIMIT:
                raise core.BundleError('native_test_state_limit')
    return total


def _command(argv, env, profile, work, deadline):
    remaining = min(30, deadline - time.monotonic())
    if remaining <= 0:
        raise core.BundleError('native_stage_deadline')
    end = time.monotonic() + remaining
    command = ['/usr/bin/sandbox-exec', '-p', profile, *map(str, argv)]
    buffers = [bytearray(), bytearray()]
    with subprocess.Popen(command, cwd=work, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, start_new_session=False) as process:
        streams = {process.stdout: 0, process.stderr: 1}
        for stream in streams:
            os.set_blocking(stream.fileno(), False)
        try:
            while streams:
                left = end - time.monotonic()
                if left <= 0:
                    raise core.BundleError('native_stage_deadline')
                ready, _, _ = select.select(list(streams), [], [], min(left, 0.05))
                for stream in ready:
                    raw = os.read(stream.fileno(), 65536)
                    if not raw:
                        del streams[stream]
                        continue
                    buffer = buffers[streams[stream]]
                    buffer.extend(raw)
                    if len(buffer) > 1 << 20:
                        raise core.BundleError('native_diagnostic_size_limit')
                _state_size(work)
            code = process.wait(timeout=max(0, end - time.monotonic()))
            return code, bytes(buffers[0]), bytes(buffers[1])
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=1)


def _sandbox_diagnostics(code, output, error, expected=None):
    # Fixed indicators only: never copy a path, secret, exception or output snippet.
    scanned = error[:4096].lower() if type(error) is bytes else b''
    markers = (
        ('operation_not_permitted', b'operation not permitted'),
        ('permission_denied', b'permission denied'),
        ('sandbox_apply', b'sandbox_apply'), ('sandbox_init', b'sandbox_init'),
        ('syntax_error', b'syntax error'), ('parse_error', b'parse error'),
        ('file_not_found', b'no such file or directory'), ('dyld', b'dyld'),
    )
    return {
        'exit_code': code if type(code) is int and -255 <= code <= 255 else None,
        'stdout_bytes': len(output) if type(output) is bytes else None,
        'stderr_bytes': len(error) if type(error) is bytes else None,
        'stdout_matches_expected': (type(output) is bytes and output == expected) if expected is not None else None,
        'stderr_scanned_bytes': len(scanned),
        'stderr_scan_truncated': type(error) is bytes and len(error) > 4096,
        'stderr_markers': [name for name, fragment in markers if fragment in scanned],
    }


def _fixture(work, deadline):
    # Reuse the already-tested synthetic producer fixture, never operator data.
    import pytest
    from tests.test_group_a_backup_acquisition import setup
    from tests.test_group_a_backup_prefix import capture, run
    root = work / 'fixture-source'
    root.mkdir(mode=0o700)
    generator = setup.__wrapped__(root)
    patch = pytest.MonkeyPatch()
    try:
        data = next(generator)
        patch.setenv('CBP_STATE_DIR', str(work / 'python-state'))
        captured = capture(data, patch, shared=work / 'shared-objects')
        result = run(data, shared_object_roots={data['sources'][0].account: work / 'shared-objects'}, deadline=deadline)
        if result.bundle.total_bytes > INPUT_LIMIT:
            raise core.BundleError('native_synthetic_input_limit')
        return result, data['sources'][0].account, captured['relativepath']
    finally:
        patch.undo()
        generator.close()


def _wrong_key_rejected(code):
    # Restic0.19.1 documents12 specifically; generic failure is not key proof.
    return type(code) is int and code == 12


def _corruption_rejected(code, output, pack):
    if type(code) is not int or code != 1:
        return False
    try:
        rows = [core._json(line) for line in output.splitlines() if line.strip()]
        summaries = [row for row in rows if type(row) is dict and row.get('message_type') == 'summary']
        return (len(summaries) == 1 and type(summaries[0].get('num_errors')) is int
                and summaries[0]['num_errors'] > 0 and type(summaries[0].get('broken_packs')) is list
                and pack in summaries[0]['broken_packs'])
    except Exception:
        return False


def _worker(directory, receipt_sha, pins_path, pins_sha, parent, deadline):
    phase = 'verify_inputs'
    diagnostics = None
    try:
        parent = core._private(Path(parent))
        work = parent / 'work'
        work.mkdir(mode=0o700)
        paths, receipt = verify_tools(Path(directory), receipt_sha, Path(pins_path), pins_sha, deadline)
        for name, source_path in paths.items():
            target = parent / 'bin' / name
            with core._reader(source_path) as source, core._new_file(target) as out:
                tools._copy_binary(source, out, tools.MAX_BINARY[name], deadline)
                out.flush()
                os.fsync(out.fileno())
            if core._file_hash(target, limit=tools.MAX_BINARY[name], deadline=deadline, clock=time.monotonic)[1] != receipt['tools'][name]['binary_sha256']:
                raise core.BundleError('native_tool_copy_changed')
            target.chmod(0o500)  # Only new owned copies, never the staged originals.
        for name in ('home', 'tmp', 'config', 'cache'):
            (work / name).mkdir(mode=0o700)
        core._bytes_file(work / 'config/rclone.conf', b'[fixture]\ntype = local\n')
        core._bytes_file(work / 'inside-canary', b'CRYPTKEEP_SYNTHETIC_CANARY\n')
        core._bytes_file(parent / 'outside-canary', b'CRYPTKEEP_SYNTHETIC_CANARY\n')
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(work / 'home'), 'TMPDIR': str(work / 'tmp'),
            'LC_ALL': 'C', 'RCLONE_CONFIG': str(work / 'config/rclone.conf'), 'RESTIC_PASSWORD': secrets.token_hex(32)}
        profile = sandbox_profile(parent)
        phase = 'sandbox_positive'
        code, out, error = _command(['/bin/cat', work / 'inside-canary'], env, profile, work, deadline)
        diagnostics = _sandbox_diagnostics(code, out, error, b'CRYPTKEEP_SYNTHETIC_CANARY\n')
        if code != 0 or out != b'CRYPTKEEP_SYNTHETIC_CANARY\n':
            raise core.BundleError('native_sandbox_unavailable')
        phase = 'sandbox_file_denial'
        diagnostics = None
        code, out, error = _command(['/bin/cat', parent / 'outside-canary'], env, profile, work, deadline)
        diagnostics = _sandbox_diagnostics(code, out, error)
        if code == 0 or not any(s in error for s in (b'Operation not permitted', b'Permission denied')):
            raise core.BundleError('native_sandbox_file_denial_unproved')
        phase = 'sandbox_network_denial'
        diagnostics = None
        canary = ('import socket,sys\ntry:\n s=socket.socket();s.bind(("127.0.0.1",0))\n'
                  'except PermissionError:\n print("NETWORK_DENIED")\nelse:\n s.close();sys.exit(7)\n')
        code, out, error = _command(['/usr/bin/python3', '-I', '-S', '-B', '-c', canary], env, profile, work, deadline)
        diagnostics = _sandbox_diagnostics(code, out, error, b'NETWORK_DENIED\n')
        if code != 0 or out != b'NETWORK_DENIED\n':
            raise core.BundleError('native_sandbox_network_denial_unproved')
        phase = 'build_synthetic_fixture'
        # This function runs only in the owned worker. Keep module-level stores
        # and replay imports on synthetic state after fixture patches unwind.
        os.environ['CBP_STATE_DIR'] = str(work / 'python-state')
        captured, account, journal = _fixture(work, deadline)
        repo = work / 'encrypted-repository'
        common = [str(parent / 'bin/restic'), '--cache-dir', str(work / 'cache'), '-r', 'rclone:fixture:' + str(repo),
            '-o', 'rclone.program=' + str(parent / 'bin/rclone'),
            '-o', 'rclone.args=serve restic --stdio --retries 1 --low-level-retries 1 --contimeout 5s --timeout 20s']
        for phase, command in [('native_init', ['init']), ('native_backup', ['--json', 'backup', str(captured.bundle.directory)]),
                               ('native_read_data_check', ['check', '--read-data'])]:
            code, out, _ = _command([*common, *command], env, profile, work, deadline)
            if code != 0:
                raise core.BundleError('native_positive_stage_failed')
            if phase == 'native_backup':
                summaries = [core._json(line) for line in out.splitlines() if line.strip()]
                ids = [s.get('snapshot_id') for s in summaries if type(s) is dict and s.get('message_type') == 'summary']
                if len(ids) != 1:
                    raise core.BundleError('native_snapshot_identity_missing')
                snapshot = core._sha(ids[0])
        phase = 'native_wrong_key'
        code, _, _ = _command([*common, 'snapshots'], {**env, 'RESTIC_PASSWORD': secrets.token_hex(32)}, profile, work, deadline)
        if not _wrong_key_rejected(code):
            raise core.BundleError('native_wrong_key_not_rejected')
        phase = 'native_restore'
        restored = work / 'restored'
        if restored.exists():
            raise core.BundleError('native_restore_destination_exists')
        code, _, _ = _command([*common, 'restore', snapshot, '--target', str(restored)], env, profile, work, deadline)
        if code != 0:
            raise core.BundleError('native_restore_failed')
        phase = 'restored_manifest_and_replay'
        restored_bundle = restored / captured.bundle.directory.relative_to('/')
        limits = core.BundleLimits(500, 40_000_000, 5_000_000)
        core.verify_bundle(restored_bundle, expected_manifest_sha256=captured.bundle.manifest_sha256,
            limits=limits, deadline=deadline)
        full_journal = account + '/data/' + journal
        directories = prefix.restored_recording_directories(restored_bundle, account=account, journal_path=full_journal,
            expected_manifest_sha256=captured.bundle.manifest_sha256, limits=limits, deadline=deadline)
        from services.strategies import signal_input_capture as capture
        replayed = 0
        for record in capture.iter_runner_records(restored_bundle / full_journal):
            result = capture.replay_runner_decision(record, object_directory=directories[record['payload']['object_scope']])
            if result.get('decision_match') is not True:
                raise core.BundleError('native_restored_replay_failed')
            replayed += 1
        if replayed != 1:
            raise core.BundleError('native_replay_count_changed')
        phase = 'ciphertext_corruption_check'
        _state_size(work)
        corrupt = work / 'corrupt-repository'
        shutil.copytree(repo, corrupt)
        packs = sorted((corrupt / 'data').glob('*/*'))
        if not packs or not packs[0].is_file():
            raise core.BundleError('native_ciphertext_pack_missing')
        with packs[0].open('r+b') as stream:
            byte = stream.read(1)
            if not byte:
                raise core.BundleError('native_ciphertext_pack_empty')
            stream.seek(0)
            stream.write(bytes([byte[0] ^ 1]))
        corrupt_common = list(common)
        corrupt_common[corrupt_common.index('-r') + 1] = 'rclone:fixture:' + str(corrupt)
        code, output, _ = _command([*corrupt_common, '--json', 'check', '--read-data'], env, profile, work, deadline)
        if not _corruption_rejected(code, output, packs[0].name):
            raise core.BundleError('native_corrupt_ciphertext_not_rejected')
        size = _state_size(work)
        core._budget(deadline, time.monotonic)
        return {'status': 'COMPLETE', 'local_encrypted_recovery': True, 'offsite_verified': False,
            'manifest_sha256': captured.bundle.manifest_sha256, 'replayed': replayed,
            'wrong_key_rejected': True, 'modified_ciphertext_rejected': True, 'measured_state_bytes': size}
    except Exception as exc:
        result = {'status': 'INCOMPLETE', 'phase': phase, 'offsite_verified': False}
        if phase in ('sandbox_positive', 'sandbox_file_denial', 'sandbox_network_denial'):
            reason = 'unclassified_sandbox_failure'
            known = ('native_sandbox_unavailable', 'native_sandbox_file_denial_unproved',
                     'native_sandbox_network_denial_unproved', 'native_stage_deadline',
                     'native_diagnostic_size_limit', 'native_test_state_limit', 'unsafe_native_test_state')
            if (isinstance(exc, core.BundleError) and len(exc.args) == 1
                    and type(exc.args[0]) is str and exc.args[0] in known):
                reason = exc.args[0]
            elif isinstance(exc, OSError):
                reason = 'os_error'
            error_number = exc.errno if isinstance(exc, OSError) else None
            result['diagnostics'] = {
                'reason': reason,
                'errno': error_number if type(error_number) is int and 0 < error_number < 4096 else None,
                'command': diagnostics,
            }
        return result


def main(argv=None, *, executor=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--receipt-sha256', required=True)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--pins-sha256', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({'status': 'INCOMPLETE', 'reason': 'native_execution_not_requested', 'clients_executed': False}))
        return 1
    attempt_deadline = time.monotonic() + 300
    parent = None
    try:
        # Anchor to invocation cwd; the worker still rejects symlinks/noncanonical paths.
        pins_path = args.pins if args.pins.is_absolute() else Path.cwd() / args.pins
        # Image verification is the worker's first phase, inside its deadline.
        parent = Path(tempfile.mkdtemp(prefix='cryptkeep-backup-native-', dir='/private/tmp'))
        parent.chmod(0o700)
        remaining = attempt_deadline - time.monotonic()
        if remaining < 0.5:
            raise core.BundleError('native_attempt_budget_exhausted_before_worker')
        result = (executor or OwnedProcessExecutor()).call(_worker,
            (str(args.tools), args.receipt_sha256, str(pins_path), args.pins_sha256, str(parent), attempt_deadline - 30), remaining)
        print(json.dumps({**result, 'owned_directory': str(parent)}, sort_keys=True))
        return 0 if result.get('status') == 'COMPLETE' else 1
    except (Exception, KeyboardInterrupt):
        print(json.dumps({'status': 'INCOMPLETE', 'phase': 'controller_or_cleanup', 'offsite_verified': False,
                          'owned_directory': str(parent) if parent is not None else None}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
