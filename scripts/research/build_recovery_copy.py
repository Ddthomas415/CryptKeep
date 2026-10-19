"""Local screened recovery copy; no Git writes, execution, cleanup or publishing.

Screening is heuristic, not certification that arbitrary files contain no secrets.
Credential/runtime paths, possible secrets and unsupported opaque files are omitted
with explicit reasons. Originals and earlier manifests are never changed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import subprocess
import tarfile
from datetime import datetime, timezone
import zipfile

from services.audit.backup_artifact_secret_scan import _BYTE_PATTERNS

MAX_FILE = 160 * 1024**2
MAX_EXPANDED = 512 * 1024**2
DENIED_DIRS = {'.git', '.ssh', '.aws', '.codex', '.agents', '.cbp_state',
               '.cbp_state_challengers', '.venv', 'venv', '__pycache__',
               '.pytest_cache', '.ruff_cache', 'node_modules', 'build', 'dist',
               '_claude_ops'}
ROOT_DENIED_DIRS = {'runtime', 'logs', 'data'}
DENIED_NAMES = {'user.yaml', '.browser-access-token', '.browser-compose-override.json',
                'id_rsa', 'id_ed25519', '.DS_Store', '.coverage',
                'credentials.json', 'credentials.yaml', 'credentials.yml'}
COMPANION_PUBLIC = {
    f'phase1_research_copilot/{service}/{name}.py'
    for service in ('market_data', 'archive_lookup', 'audit_log', 'news_ingestion',
                    'memory_retrieval', 'parser_normalizer', 'risk_stub', 'orchestrator', 'gateway')
    for name in ('__init__', 'main')
} | {
    f'phase1_research_copilot/shared/{name}.py'
    for name in ('__init__', 'answer_metadata', 'logging', 'db', 'config', 'audit',
                 'models', 'tools', 'prompting', 'retry', 'llm_client', 'probe', 'public_fetch')
} | {
    'phase1_research_copilot/' + name for name in (
        'memory_retrieval/article_view.py', 'memory_retrieval/question_query.py',
        'scripts/smoke_phase1_copilot.py', 'requirements.txt', 'README.md',
        'contracts/service_contracts.md', 'Dockerfile.service', 'docker-compose.yml',
        '.dockerignore', 'Dockerfile.service.ad18488df_original',
        'docker-compose.yml.ad18488df_original', 'news_ingestion/main.py.ad18488df_original',
        'memory_retrieval/main.py.ad18488df_original')
}
PUBLIC_DATABASES = {
    f'research/{study}/public_archive.sqlite' for study in (
        'coinbase_confirmation_usd_v1', 'coinbase_confirmation_v1',
        'coinbase_retrospective_20261009', 'multisymbol_baseline_v1')
}
OPAQUE = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.icns', '.pdf', '.dmg', '.exe',
          '.pyc', '.pyo', '.pyd', '.sqlite-wal', '.sqlite-shm'}
EXTRA = (
    ('slack_webhook', re.compile(rb'https://hooks\.slack\.com/services/[A-Za-z0-9/]+')),
    ('extended_openai_key', re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}\b')),
    ('literal_secret_assignment', re.compile(
        rb'''(?i)(?:api[_-]?key|secret|token|password)\s*["']?\s*[:=]\s*["'][A-Za-z0-9/+_-]{20,}["']''')),
)


def safe_rel(value):
    p = PurePosixPath(value)
    if not value or not p.parts or p.is_absolute() or '..' in p.parts or '\\' in value or '\0' in value:
        raise ValueError('unsafe_relative_path')
    return p.as_posix()


def denied(value):
    p = PurePosixPath(safe_rel(value))
    return (p.parts[0] in ROOT_DENIED_DIRS
            or any(x in DENIED_DIRS or x.startswith('.venv') for x in p.parts)
            or p.name in DENIED_NAMES or p.name.startswith(('.env', '.browser'))
            or p.suffix.lower() in {'.env', '.pem', '.key', '.p12', '.pfx', '.log', '.swp', '.tmp'})


def outside_public_scope(rel):
    return ((rel.startswith('phase1_research_copilot/') and rel not in COMPANION_PUBLIC)
            or (rel.startswith('research/') and PurePosixPath(rel).name == 'public_archive.sqlite'
                and rel not in PUBLIC_DATABASES))


def archive_kind(data):
    # A rename cannot turn an archive containing .env into accepted plain text.
    if zipfile.is_zipfile(io.BytesIO(data)):
        return 'zip'
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:*'):
            return 'tar'
    except (ValueError, OSError, tarfile.TarError, EOFError):
        return None


def screened_reason(data, name, depth=0):
    """Return a fixed reason only; never return a matching value or its hash."""
    if len(data) > MAX_FILE or depth > 2:
        return 'inspection_limit'
    for reason, pattern in (*_BYTE_PATTERNS, *EXTRA):
        if pattern.search(data):
            return 'possible_secret:' + reason
    suffix = PurePosixPath(name).suffix.lower()
    if suffix in OPAQUE:
        return 'opaque_content_not_cleared'
    kind = archive_kind(data)
    if kind == 'zip':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                members = archive.infolist()
                if len(members) > 20000 or sum(m.file_size for m in members) > MAX_EXPANDED:
                    return 'inspection_limit'
                names = set()
                for m in members:
                    if m.filename in ('.', './'):
                        if (m.is_dir() and stat.S_ISDIR(m.external_attr >> 16)
                                and m.file_size == 0 and not m.flag_bits & 1):
                            continue
                        return 'archive_member_refused'
                    rel = safe_rel(m.filename)
                    if rel in names or denied(rel) or m.flag_bits & 1 or stat.S_ISLNK(m.external_attr >> 16):
                        return 'archive_member_refused'
                    names.add(rel)
                    if m.is_dir() and m.file_size != 0:
                        return 'archive_member_refused'
                    if not m.is_dir():
                        reason = screened_reason(archive.read(m), rel, depth + 1)
                        if reason:
                            return reason
        except (ValueError, OSError, zipfile.BadZipFile, RuntimeError):
            return 'archive_unreadable'
    elif kind == 'tar':
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as archive:
                total, count, names = 0, 0, set()
                for m in archive:
                    total, count = total + m.size, count + 1
                    if total > MAX_EXPANDED or count > 20000 or m.size > MAX_FILE:
                        return 'inspection_limit'
                    if m.isdir() and m.size != 0:
                        return 'archive_member_refused'
                    if m.isdir() and m.name in ('.', './'):
                        continue
                    rel = safe_rel(m.name)
                    if rel in names or denied(rel) or not (m.isfile() or m.isdir()):
                        return 'archive_member_refused'
                    names.add(rel)
                    if m.isfile():
                        reason = screened_reason(archive.extractfile(m).read(MAX_FILE + 1), rel, depth + 1)
                        if reason:
                            return reason
        except (ValueError, OSError, tarfile.TarError, EOFError):
            return 'archive_unreadable'
    elif suffix in {'.zip', '.docx', '.xlsx', '.xz', '.gz', '.tar', '.tgz'}:
        return 'archive_unreadable'
    elif suffix not in {'.sqlite', '.db'}:
        try:
            data.decode('utf-8')
        except UnicodeError:
            return 'opaque_content_not_cleared'
        if b'\0' in data:
            return 'opaque_content_not_cleared'
    return None


def read_regular(root, rel):
    """Open each component without following links; retain stable-file evidence."""
    parts = PurePosixPath(safe_rel(rel)).parts
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE:
                raise ValueError('source_not_bounded_regular_file')
            data = stream.read(MAX_FILE + 1)
            after = os.fstat(stream.fileno())
            identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
            if len(data) != before.st_size or identity(after) != identity(before):
                raise ValueError('source_changed_during_read')
            return data, before
    finally:
        os.close(directory)


def inventory(root):
    command = ['git', '--no-optional-locks', '-C', str(root), 'ls-files', '-z',
               '--cached', '--others', '--exclude-standard']
    raw = subprocess.run(command, check=True, capture_output=True).stdout
    paths = {os.fsdecode(p) for p in raw.split(b'\0') if p}
    paths.update(p for p in COMPANION_PUBLIC | PUBLIC_DATABASES if (root / p).exists())
    return sorted(p for p in paths if not outside_public_scope(p))


def restore_verified(archive_path, destination, entries):
    destination.mkdir(mode=0o700)
    expected = {r['path']: r for r in entries}
    seen = set()
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive:
            rel = safe_rel(member.name)
            if not member.isfile() or rel in seen or rel not in expected:
                raise ValueError('restore_member_refused')
            row = expected[rel]
            if member.size != row['bytes'] or member.size > MAX_FILE:
                raise ValueError('restore_size_mismatch')
            data = archive.extractfile(member).read(MAX_FILE + 1)
            if hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('restore_hash_mismatch')
            target = destination / rel
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data)
            target.chmod(row['recovery_mode'])
            seen.add(rel)
    if seen != set(expected):
        raise ValueError('restore_member_missing')
    return len(seen)


def build(root, output, paths=None):
    root, output = Path(root).resolve(strict=True), Path(output).absolute()
    if output.parent.resolve(strict=True) != output.parent or output.is_relative_to(root):
        raise ValueError('recovery_must_be_outside_repo_in_canonical_parent')
    output.mkdir(mode=0o700)
    selected = inventory(root) if paths is None else sorted(set(paths))
    files = output / 'files'
    files.mkdir(mode=0o700)
    included, excluded = [], []
    for rel in selected:
        rel = safe_rel(rel)
        reason = 'credential_or_runtime_path' if denied(rel) else None
        if reason is None and outside_public_scope(rel):
            reason = 'outside_reviewed_public_scope'
        if reason is None and PurePosixPath(rel).suffix.lower() in {'.sqlite', '.db'}:
            if any((root / (rel + tail)).exists() for tail in ('-wal', '-journal')):
                reason = 'database_journal_present'
        if reason is None:
            try:
                data, metadata = read_regular(root, rel)
                reason = screened_reason(data, rel)
            except (OSError, ValueError):
                reason = 'source_unreadable_or_changed'
        if reason:
            excluded.append({'path': rel, 'reason': reason})
            continue
        target = files / rel
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        mode = 0o700 if metadata.st_mode & 0o111 else 0o600
        target.chmod(mode)
        included.append({'path': rel, 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest(), 'recovery_mode': mode})
    # Retain only consistent selected files; do not claim a concurrent global snapshot.
    for row in included:
        data, _ = read_regular(root, row['path'])
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('source_changed_before_seal')
        if PurePosixPath(row['path']).suffix.lower() in {'.sqlite', '.db'} and any(
                (root / (row['path'] + tail)).exists() for tail in ('-wal', '-journal')):
            raise ValueError('database_journal_appeared_before_seal')
    archive_path = output / 'recovery.tar.gz'
    with archive_path.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz', compresslevel=1) as archive:
        for row in included:
            member = tarfile.TarInfo(row['path'])
            member.size, member.mode, member.mtime = row['bytes'], row['recovery_mode'], 0
            with (files / row['path']).open('rb') as source:
                archive.addfile(member, source)
    restored = restore_verified(archive_path, output / 'restored', included)
    checks = []
    for row in included:
        target = output / 'restored' / row['path']
        if hashlib.sha256(target.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('restored_file_hash_mismatch')
        if target.suffix == '.sqlite':
            with sqlite3.connect(target.as_uri() + '?mode=ro&immutable=1', uri=True) as connection:
                if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                    raise ValueError('restored_database_invalid')
            checks.append(row['path'])
    manifest = {'schema': 'screened-selected-recovery-v1',
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'root': str(root), 'files': included, 'exclusions': excluded,
                'restored_files_verified': restored, 'restored_databases_checked': checks,
                'complete_repository_or_secret_clearance': False,
                'runtime_or_environment_restore_tested': False,
                'screening': 'Path exclusions and heuristic byte patterns; nested archives inspected within bounds. No OCR or universal secret guarantee.',
                'originals_modified': False, 'git_mutated': False}
    with (output / 'refreshed_checkpoint.csv').open('x', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['path', 'disposition', 'bytes', 'sha256', 'reason'])
        writer.writerows((r['path'], 'copied_verified', r['bytes'], r['sha256'], '') for r in included)
        writer.writerows((r['path'], 'excluded', '', '', r['reason']) for r in excluded)
    with (output / 'backup_manifest.json').open('x') as stream:
        stream.write(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root, args.output)
    print(json.dumps({'output': str(args.output), 'restored_verified': result['restored_files_verified'],
                      'excluded': len(result['exclusions']), 'complete_repository_or_secret_clearance': False}))


if __name__ == '__main__':
    main()
