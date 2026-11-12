"""Bounded official-tool staging, not execution, installation or authentication."""
import bz2
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import select
import stat
import struct
import subprocess
import time
import zipfile

from services.control import group_a_backup_bundle as core

MAX_DOWNLOAD = 200 << 20
MAX_BINARY = {'restic': 64 << 20, 'rclone': 128 << 20}


def load_pins(path, expected_sha256):
    path = Path(path)
    if path.resolve(strict=True) != path:
        raise core.BundleError('unsafe_tool_pin_path')
    with path.open('rb') as source:
        raw = source.read(16385)
    if len(raw) > 16384 or hashlib.sha256(raw).hexdigest() != core._sha(expected_sha256):
        raise core.BundleError('tool_pins_changed')
    pins = core._json(raw)
    if (type(pins) is not dict or set(pins) != {'format', 'platform', 'signature_verified', 'tools'}
            or type(pins['format']) is not int or pins['format'] != 1
            or pins['platform'] != 'darwin_arm64' or pins['signature_verified'] is not False
            or type(pins['tools']) is not dict or set(pins['tools']) != set(MAX_BINARY)):
        raise core.BundleError('invalid_tool_pins')
    total = 0
    for name, item in pins['tools'].items():
        if (type(item) is not dict or set(item) != {'version', 'archive', 'bytes', 'sha256',
                'checksums_bytes', 'checksums_sha256'} or type(item['version']) is not str
                or re.fullmatch(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', item['version']) is None):
            raise core.BundleError('invalid_tool_release')
        version = item['version']
        expected = (f'restic_{version}_darwin_arm64.bz2' if name == 'restic'
                    else f'rclone-v{version}-osx-arm64.zip')
        if (item['archive'] != expected or type(item['bytes']) is not int or not 0 < item['bytes'] < MAX_DOWNLOAD
                or type(item['checksums_bytes']) is not int or not 0 < item['checksums_bytes'] <= 16384):
            raise core.BundleError('invalid_tool_archive')
        core._sha(item['sha256'])
        core._sha(item['checksums_sha256'])
        total += item['bytes'] + item['checksums_bytes']
    if total > MAX_DOWNLOAD:
        raise core.BundleError('tool_download_budget')
    return pins


def _url(name, item, member):
    return f'https://github.com/{name}/{name}/releases/download/v{item["version"]}/{member}'


def _fetch(url, output, size, deadline, home):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise core.BundleError('tool_download_deadline')
    # --disable is first: never inherit .curlrc, auth, proxies or debug settings.
    command = ['/usr/bin/curl', '--disable', '--proto', '=https', '--proto-redir', '=https',
        '--location', '--max-redirs', '3', '--fail', '--silent', '--show-error',
        '--connect-timeout', '5', '--max-time', str(remaining), '--max-filesize', str(size), url]
    with subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, env={'PATH': '/usr/bin:/bin', 'HOME': str(home)},
            close_fds=True, start_new_session=False) as process:
        try:
            os.set_blocking(process.stdout.fileno(), False)
            transferred = 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([process.stdout], [], [], remaining)[0]:
                    raise core.BundleError('official_download_deadline')
                raw = os.read(process.stdout.fileno(), min(1 << 20, size - transferred + 1))
                if not raw:
                    break
                transferred += len(raw)
                if transferred > size or output.write(raw) != len(raw):
                    raise core.BundleError('official_download_size_or_write_limit')
            if process.wait(timeout=max(0, deadline - time.monotonic())) != 0:
                raise core.BundleError('official_download_failed')
        except BaseException:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=1)
            raise


def _download(path, url, size, digest, deadline, fetch):
    core._budget(deadline, time.monotonic)
    with core._new_file(path) as output:
        fetch(url, output, size, deadline, path.parent.parent)
        output.flush()
        os.fsync(output.fileno())
    actual_size, actual_digest = core._file_hash(path, limit=size, deadline=deadline, clock=time.monotonic)
    if (actual_size, actual_digest) != (size, digest):
        raise core.BundleError('official_download_identity_changed')


def _checksum(raw, item):
    matches = re.findall(rb'^([0-9a-f]{64})[ \t]+\*?' + re.escape(item['archive'].encode()) + rb'\r?$', raw, re.M)
    if len(matches) != 1 or matches[0].decode() != item['sha256']:
        raise core.BundleError('published_checksum_mismatch')


def _copy_binary(source, output, limit, deadline):
    total = 0
    while True:
        core._budget(deadline, time.monotonic)
        raw = source.read(min(1 << 20, limit - total + 1))
        if not raw:
            break
        total += len(raw)
        if total > limit or output.write(raw) != len(raw):
            raise core.BundleError('tool_binary_size_or_write_limit')


def _extract(archive, destination, name, item, deadline):
    with core._new_file(destination) as output:
        if name == 'restic':
            with bz2.BZ2File(archive, 'rb') as source:
                _copy_binary(source, output, MAX_BINARY[name], deadline)
        else:
            with archive.open('rb') as source:
                source.seek(max(0, archive.stat().st_size - 65557))
                tail = source.read(65557)
            offset = tail.rfind(b'PK\x05\x06')
            if offset < 0 or len(tail) - offset < 22:
                raise core.BundleError('invalid_tool_zip_directory')
            _, disk, directory_disk, entries_here, entries, size, _, comment = struct.unpack('<4s4H2IH', tail[offset:offset + 22])
            if (disk != 0 or directory_disk != 0 or entries_here != entries or not 1 <= entries <= 64
                    or size > 65536 or offset + 22 + comment != len(tail)):
                raise core.BundleError('oversize_or_multidisk_tool_zip')
            expected = f'rclone-v{item["version"]}-osx-arm64/rclone'
            with zipfile.ZipFile(archive) as package:
                members = package.infolist()
                seen = set()
                for info in members:
                    path = PurePosixPath(info.filename)
                    mode = info.external_attr >> 16
                    if (path.is_absolute() or '..' in path.parts or '\\' in info.filename
                            or info.filename in seen or info.flag_bits & 1
                            or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                        raise core.BundleError('unsafe_tool_zip_member')
                    seen.add(info.filename)
                selected = [m for m in members if m.filename == expected]
                if len(selected) != 1 or selected[0].is_dir() or selected[0].file_size > MAX_BINARY[name]:
                    raise core.BundleError('missing_or_oversize_tool_zip_binary')
                with package.open(selected[0]) as source:
                    _copy_binary(source, output, MAX_BINARY[name], deadline)
        output.flush()
        os.fsync(output.fileno())
    with core._reader(destination) as source:
        header = source.read(32)
    if len(header) != 32 or struct.unpack('<I', header[:4])[0] != 0xfeedfacf:
        raise core.BundleError('tool_not_thin_macho64')
    fields = struct.unpack('<8I', header)
    if fields[1] != 0x0100000c or fields[3] != 2:
        raise core.BundleError('tool_not_arm64_executable')
    return core._file_hash(destination, limit=MAX_BINARY[name], deadline=deadline, clock=time.monotonic)


def prepare(parent, *, pins_path, pins_sha256, deadline, fetch=_fetch):
    """Network/download action only when explicitly called; clients never run.

    Use a separately owned hard-deadline process for the authorized invocation.
    Local file/verification bounds here are cooperative. Preserve partial output.
    """
    try:
        core._budget(deadline, time.monotonic)
        pins = load_pins(pins_path, pins_sha256)
        root = core._new_directory(parent, 'tools-', 'darwinarm64')
        receipts = {}
        for name in ('restic', 'rclone'):
            item = pins['tools'][name]
            checksums = root / 'archives' / (name + '-SHA256SUMS')
            _download(checksums, _url(name, item, 'SHA256SUMS'), item['checksums_bytes'],
                      item['checksums_sha256'], deadline, fetch)
            _checksum(checksums.read_bytes(), item)
            archive = root / 'archives' / item['archive']
            _download(archive, _url(name, item, item['archive']), item['bytes'], item['sha256'], deadline, fetch)
            executable = root / 'bin' / name
            size, digest = _extract(archive, executable, name, item, deadline)
            receipts[name] = {'version': item['version'], 'archive_sha256': item['sha256'],
                'binary_sha256': digest, 'binary_bytes': size, 'relative_path': 'bin/' + name,
                'mode': '0600_NOT_EXECUTABLE'}
        core._sync_artifact_directories(root, ['archives/' + pins['tools'][n]['archive'] for n in receipts]
            + ['archives/' + n + '-SHA256SUMS' for n in receipts] + ['bin/' + n for n in receipts],
            deadline, time.monotonic)
        receipt = {'format': 1, 'platform': 'darwin_arm64', 'pins_sha256': pins_sha256,
            'tools': receipts, 'clients_executed': False, 'signature_verified': False,
            'provenance': 'official_https_api_and_published_checksums', 'native_execution_authorized': False}
        core._budget(deadline, time.monotonic)
        core._bytes_file(root / 'TOOLCHAIN.json', core._encode(receipt))
        core._sync_directory(root)
        core._sync_directory(root.parent)
        core._budget(deadline, time.monotonic)
        return {'directory': str(root), 'receipt_sha256': hashlib.sha256(core._encode(receipt)).hexdigest(), **receipt}
    except core.BundleError:
        raise
    except Exception:
        raise core.BundleError('tool_preparation_failed_or_commit_uncertain') from None
