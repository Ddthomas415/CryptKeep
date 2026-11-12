"""Synthetic archive preparation only; no curl, download or native client run."""
import bz2
import hashlib
import io
import json
import os
import stat
import struct
import time
import zipfile

import pytest

from services.control import group_a_backup_bundle as core
from services.control import group_a_backup_tools as tools


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def macho(cpu=0x0100000c):
    return struct.pack('<8I', 0xfeedfacf, cpu, 0, 2, 0, 0, 0, 0) + b'SYNTHETIC-not-executed'


def package(raw, *, member='rclone-v9.8.7-osx-arm64/rclone', mode=stat.S_IFREG | 0o755, duplicate=False):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as archive:
        info = zipfile.ZipInfo(member)
        info.external_attr = mode << 16
        archive.writestr(info, raw)
        if duplicate:
            archive.writestr(info, raw)
    return out.getvalue()


@pytest.fixture
def inputs(tmp_path):
    raw_archives = {'restic': bz2.compress(macho()), 'rclone': package(macho())}
    pins = {'format': 1, 'platform': 'darwin_arm64', 'signature_verified': False, 'tools': {}}
    payloads = {}
    for name, raw in raw_archives.items():
        archive = 'restic_9.8.7_darwin_arm64.bz2' if name == 'restic' else 'rclone-v9.8.7-osx-arm64.zip'
        checksums = (sha(raw) + '  ' + archive + '\n').encode()
        item = {'version': '9.8.7', 'archive': archive, 'bytes': len(raw), 'sha256': sha(raw),
                'checksums_bytes': len(checksums), 'checksums_sha256': sha(checksums)}
        pins['tools'][name] = item
        payloads[tools._url(name, item, archive)] = raw
        payloads[tools._url(name, item, 'SHA256SUMS')] = checksums
    path = tmp_path / 'pins.json'
    path.write_bytes(json.dumps(pins).encode())
    parent = tmp_path / 'private'
    parent.mkdir(mode=0o700)
    calls = []
    def fetch(url, output, size, deadline, home):
        calls.append(url)
        output.write(payloads[url])
    return dict(path=path, parent=parent, pins=pins, payloads=payloads, fetch=fetch, calls=calls)


def prepare(inputs, **kwargs):
    return tools.prepare(inputs['parent'], pins_path=inputs['path'], pins_sha256=sha(inputs['path'].read_bytes()),
        deadline=kwargs.pop('deadline', time.monotonic() + 10), fetch=kwargs.pop('fetch', inputs['fetch']), **kwargs)


def test_exact_pinned_archives_stage_two_nonexecutable_clients(inputs):
    result = prepare(inputs)
    root = inputs['parent'] / 'tools-darwinarm64'
    assert len(inputs['calls']) == 4
    assert result['clients_executed'] is False and result['signature_verified'] is False
    assert result['native_execution_authorized'] is False
    for name in ('restic', 'rclone'):
        path = root / 'bin' / name
        assert path.read_bytes() == macho()
        assert path.stat().st_mode & 0o777 == 0o600
        assert result['tools'][name]['binary_sha256'] == sha(macho())
    assert sha((root / 'TOOLCHAIN.json').read_bytes()) == result['receipt_sha256']


def test_existing_target_is_never_overwritten(inputs):
    prepare(inputs)
    inputs['calls'].clear()
    with pytest.raises(core.BundleError):
        prepare(inputs)
    assert inputs['calls'] == []


@pytest.mark.parametrize('mutate', [
    lambda p: p.update(format=True), lambda p: p.update(signature_verified=True),
    lambda p: p['tools']['restic'].update(version='../9'),
    lambda p: p['tools']['restic'].update(archive='../../private'),
    lambda p: p['tools']['restic'].update(bytes=True),
    lambda p: p['tools']['restic'].update(sha256='x' * 64),
    lambda p: p['tools']['restic'].update(checksums_bytes=999999),
])
def test_invalid_pins_refused_before_any_fetch(inputs, mutate):
    mutate(inputs['pins'])
    inputs['path'].write_bytes(json.dumps(inputs['pins']).encode())
    with pytest.raises(core.BundleError):
        prepare(inputs)
    assert inputs['calls'] == [] and list(inputs['parent'].iterdir()) == []


@pytest.mark.parametrize('failure', ['truncated', 'oversize', 'wrong_hash', 'exception'])
def test_bad_download_has_no_completion_receipt(inputs, failure):
    def fail(url, output, size, deadline, home):
        raw = inputs['payloads'][url]
        if failure == 'truncated':
            raw = raw[:-1]
        elif failure == 'oversize':
            raw += b'x'
        elif failure == 'wrong_hash':
            raw = b'x' * len(raw)
        else:
            raise OSError('SYNTHETIC-private')
        output.write(raw)
    with pytest.raises(core.BundleError) as error:
        prepare(inputs, fetch=fail)
    assert 'SYNTHETIC-private' not in str(error.value)
    assert not list(inputs['parent'].rglob('TOOLCHAIN.json'))


@pytest.mark.parametrize('failure', ['traversal', 'symlink', 'missing', 'duplicate', 'wrong_cpu'])
def test_unsafe_archive_or_wrong_binary_refused_before_receipt(inputs, failure):
    options = {'member': '../../outside'} if failure == 'traversal' else (
        {'mode': stat.S_IFLNK | 0o777} if failure == 'symlink' else
        {'member': 'other'} if failure == 'missing' else {'duplicate': True} if failure == 'duplicate' else {})
    raw = package(macho(7) if failure == 'wrong_cpu' else macho(), **options)
    item = inputs['pins']['tools']['rclone']
    item['bytes'], item['sha256'] = len(raw), sha(raw)
    checksum = (sha(raw) + '  ' + item['archive'] + '\n').encode()
    item['checksums_bytes'], item['checksums_sha256'] = len(checksum), sha(checksum)
    inputs['payloads'][tools._url('rclone', item, item['archive'])] = raw
    inputs['payloads'][tools._url('rclone', item, 'SHA256SUMS')] = checksum
    inputs['path'].write_bytes(json.dumps(inputs['pins']).encode())
    with pytest.raises(core.BundleError):
        prepare(inputs)
    assert not list(inputs['parent'].rglob('TOOLCHAIN.json'))


def test_decompression_limit_and_deadline_refuse(inputs, monkeypatch):
    monkeypatch.setitem(tools.MAX_BINARY, 'restic', 10)
    with pytest.raises(core.BundleError):
        prepare(inputs)
    assert not list(inputs['parent'].rglob('TOOLCHAIN.json'))
    with pytest.raises(core.BundleError):
        prepare(inputs, deadline=time.monotonic() - 1)


@pytest.mark.parametrize('raw', [b'', b'0' * 64 + b'  fixture\n', b'a' * 64 + b'  fixture\n' + b'a' * 64 + b'  fixture\n'])
def test_ambiguous_or_wrong_published_checksum_refused(raw):
    with pytest.raises(core.BundleError):
        tools._checksum(raw, {'archive': 'fixture', 'sha256': 'a' * 64})


def test_download_controller_requires_flag_and_uses_owned_deadline(inputs, capsys):
    from scripts.research.prepare_group_a_backup_tools import main
    args = ['--parent', str(inputs['parent']), '--pins', str(inputs['path']),
            '--pins-sha256', sha(inputs['path'].read_bytes())]
    calls = []
    class Executor:
        def call(self, fn, values, timeout):
            calls.append((fn, values, timeout))
            return {'status': 'COMPLETE', 'clients_executed': False}
    assert main(args, executor=Executor()) == 1
    assert calls == []
    assert main(args + ['--download-only'], executor=Executor()) == 0
    assert calls[0][2] == 180
    assert time.monotonic() < calls[0][1][-1] <= time.monotonic() + 160
    assert 'clients_executed' in capsys.readouterr().out


def test_download_controller_hides_raw_failure(inputs, capsys):
    from scripts.research.prepare_group_a_backup_tools import main
    class Executor:
        def call(self, *args):
            raise RuntimeError('SYNTHETIC-private')
    assert main(['--parent', str(inputs['parent']), '--pins', str(inputs['path']),
        '--pins-sha256', sha(inputs['path'].read_bytes()), '--download-only'], executor=Executor()) == 1
    assert 'SYNTHETIC-private' not in capsys.readouterr().out


@pytest.mark.parametrize('case', ['normal', 'oversize', 'nonzero', 'timeout'])
def test_real_fetch_policy_streaming_bounds_and_clean_environment(monkeypatch, tmp_path, case):
    read_fd, write_fd = os.pipe()
    raw = b'abcd' if case == 'oversize' else b'abc'
    if case != 'timeout':
        os.write(write_fd, raw)
        os.close(write_fd)
        write_fd = None
    calls = []
    class Process:
        def __init__(self, command, **kwargs):
            calls.append((command, kwargs))
            self.stdout = os.fdopen(read_fd, 'rb')
            self.code = None if case == 'timeout' else 22 if case == 'nonzero' else 0
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.stdout.close()
            if write_fd is not None:
                os.close(write_fd)
        def wait(self, **kwargs):
            return self.code
        def poll(self):
            return self.code
        def kill(self):
            self.code = -9
    monkeypatch.setattr(tools.subprocess, 'Popen', Process)
    output = io.BytesIO()
    call = lambda: tools._fetch('https://github.com/restic/restic/releases/download/v9.8.7/fixture',
        output, 3, time.monotonic() + (0.02 if case == 'timeout' else 1), tmp_path)
    if case == 'normal':
        call()
        assert output.getvalue() == b'abc'
    else:
        with pytest.raises(core.BundleError):
            call()
    command, options = calls[0]
    assert command[:2] == ['/usr/bin/curl', '--disable']
    assert options['env'] == {'PATH': '/usr/bin:/bin', 'HOME': str(tmp_path)}
    assert options['start_new_session'] is False and options['close_fds'] is True
    assert '--insecure' not in command and '--retry' not in command
