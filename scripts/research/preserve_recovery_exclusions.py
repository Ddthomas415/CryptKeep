"""Recover seven named public assets without source SQL, cleanup or execution.

Only stable main SQLite files with empty/absent WAL and no rollback journal are
supported. This is not an online WAL backup implementation or secret clearance.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tarfile

from scripts.research import build_recovery_copy as base

RAW = 'docs/research/raw_archives_20261009/'
ARCHIVES = {
    RAW + 'coinbase_hourly_last60d.tar.xz':
        '435220c4d778036ba1b3e8ac78b7817f1a372bba1f5435d32c94af9c9bf5caa5',
    RAW + 'coinbase_hourly_prior10m.tar.xz':
        '2bb417a2033b2a4b78df56db16c4471c6e1384ef23b433e276afb9108f99e6b4',
    RAW + 'cmc_weekly_and_trending.tar.xz':
        '05223937afcfb02f4c020476c8b3380fcdd7044e5f3812e4938aff858fd41f4b',
}
LOGS = {
    (RAW + 'coinbase_hourly_last60d.tar.xz', 'cb/fetch.log'): b'done 395 273\n',
    (RAW + 'coinbase_hourly_prior10m.tar.xz', 'cb2/fetch.log'): b'done 395 377\n',
}
CMC_SLUG_FILES = {
    'cmc/weekly/2026-07-19.json': '1f8a48d458d8531b379aead584212fcea02552abecd1a3bac07202bd76077fdf',
    'cmc/weekly/2026-07-26.json': 'd6555729bdeba1410ffdc12ad790fd3617ca3528fffd51099ab0f1b721a39b90',
    'cmc/weekly/2026-07-12.json': 'c87648455214bdd7d398c62d19e4004cf258129a69637ccf8425c241023a28a1',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(metadata):
    return [metadata.st_dev, metadata.st_ino, metadata.st_size,
            metadata.st_mtime_ns, metadata.st_ctime_ns]


def wal_state(root, rel):
    try:
        base.read_regular(root, rel + '-journal')
    except FileNotFoundError:
        pass
    else:
        raise ValueError('rollback_journal_present')
    try:
        data, metadata = base.read_regular(root, rel + '-wal')
    except FileNotFoundError:
        return {'wal': 'absent'}
    if data:
        raise ValueError('nonempty_wal_requires_separate_snapshot')
    return {'wal': 'empty', 'identity': identity(metadata)}


def stable_database(root, rel):
    if rel not in base.PUBLIC_DATABASES:
        raise ValueError('database_outside_named_scope')
    before = wal_state(root, rel)
    data, first = base.read_regular(root, rel)
    again, second = base.read_regular(root, rel)
    after = wal_state(root, rel)
    if before != after or identity(first) != identity(second) or data != again:
        raise ValueError('database_or_wal_changed')
    if data[:16] != b'SQLite format 3\0' or data[18:20] != b'\x02\x02':
        raise ValueError('expected_wal_mode_database')
    reason = base.screened_reason(data, rel)
    if reason:
        raise ValueError(reason)
    return data, {'database_identity': identity(first), **after}


def member_screen(data, name, source):
    """Exact public-data exceptions; returned original bytes are never rewritten."""
    if (source, name) in LOGS:
        if data != LOGS[source, name]:
            raise ValueError('public_progress_log_changed')
        return 'exact_public_progress_log'
    if source == RAW + 'cmc_weekly_and_trending.tar.xz' and name in CMC_SLUG_FILES:
        if digest(data) != CMC_SLUG_FILES[name]:
            raise ValueError('pinned_cmc_member_changed')
        rows = json.loads(data)
        matches = 0
        for row in rows:
            if (isinstance(row, list) and len(row) == 10 and row[1] == 'SKHYx'
                    and isinstance(row[2], str)
                    and base.EXTRA[1][1].fullmatch(row[2].encode())):
                # The saved fetch schema names column 2 "slug", not an API key.
                row[2] = 'PUBLIC_COIN_SLUG_CHECKED_IN_MEMORY'
                matches += 1
        if matches != 1 or base.screened_reason(json.dumps(rows).encode(), name, 1):
            raise ValueError('cmc_slug_exception_not_exclusive')
        return 'pinned_public_coin_slug'
    if base.denied(name):
        raise ValueError('archive_member_refused')
    reason = base.screened_reason(data, name, 1)
    if reason:
        raise ValueError(reason)
    return None


def inspect_archive(data, source):
    if source not in ARCHIVES or digest(data) != ARCHIVES[source]:
        raise ValueError('frozen_archive_hash_mismatch')
    seen, exceptions, total, count = set(), [], 0, 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as archive:
        for member in archive:
            total, count = total + member.size, count + 1
            if total > base.MAX_EXPANDED or count > 20000 or member.size > base.MAX_FILE:
                raise ValueError('archive_inspection_limit')
            if member.isdir() and member.size == 0 and member.name in ('.', './'):
                continue
            name = base.safe_rel(member.name)
            if name in seen or not (member.isfile() or member.isdir()):
                raise ValueError('archive_member_refused')
            seen.add(name)
            if member.isdir():
                if member.size or base.denied(name):
                    raise ValueError('archive_member_refused')
                continue
            blob = archive.extractfile(member).read(base.MAX_FILE + 1)
            exception = member_screen(blob, name, source)
            if exception:
                exceptions.append({'member': name, 'sha256': digest(blob), 'basis': exception})
    return {'members': count, 'expanded_bytes': total, 'exact_exceptions': exceptions}


def check_database(path):
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('restored_database_integrity_failed')


def build(root, output):
    root, output = Path(root).resolve(strict=True), Path(output).absolute()
    if output.parent.resolve(strict=True) != output.parent or output.is_relative_to(root):
        raise ValueError('output_must_be_new_canonical_external_directory')
    output.mkdir(mode=0o700)
    files = output / 'files'
    files.mkdir(mode=0o700)
    entries, evidence = [], {}
    for rel in sorted(base.PUBLIC_DATABASES | ARCHIVES.keys()):
        if rel in base.PUBLIC_DATABASES:
            data, detail = stable_database(root, rel)
        else:
            data, _ = base.read_regular(root, rel)
            detail = inspect_archive(data, rel)
        target = files / rel
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        target.chmod(0o600)
        if rel in base.PUBLIC_DATABASES:
            check_database(target)
        entries.append({'path': rel, 'bytes': len(data), 'sha256': digest(data), 'recovery_mode': 0o600})
        evidence[rel] = detail
    # Recheck the originals before sealing. No SQL connection touches originals.
    for row in entries:
        rel = row['path']
        if rel in base.PUBLIC_DATABASES:
            data, state = stable_database(root, rel)
            if state != evidence[rel]:
                raise ValueError('database_state_changed_before_seal')
        else:
            data, _ = base.read_regular(root, rel)
        if digest(data) != row['sha256']:
            raise ValueError('source_changed_before_seal')
    archive_path = output / 'supplement.tar.gz'
    with archive_path.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz', compresslevel=1) as archive:
        for row in entries:
            member = tarfile.TarInfo(row['path'])
            member.size, member.mode, member.mtime = row['bytes'], 0o600, 0
            with (files / row['path']).open('rb') as source:
                archive.addfile(member, source)
    restored = base.restore_verified(archive_path, output / 'restored', entries)
    for row in entries:
        target = output / 'restored' / row['path']
        if digest(target.read_bytes()) != row['sha256']:
            raise ValueError('restored_bytes_changed')
        if row['path'] in base.PUBLIC_DATABASES:
            check_database(target)
    manifest = {
        'schema': 'named-public-recovery-supplement-v1',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_root': str(root), 'files': entries, 'source_evidence': evidence,
        'restored_verified': restored, 'databases_integrity_checked': sorted(base.PUBLIC_DATABASES),
        'source_sql_connections': 0, 'complete_repository_or_secret_clearance': False,
        'limits': ['Same-disk recovery, not offsite protection or a global atomic snapshot.',
                   'Empty/absent WAL only; nonempty WAL or rollback journal refuses the copy.',
                   'Heuristic screening and exact public-member exceptions, not publication clearance.',
                   'Original files and the earlier recovery copies are not modified.'],
    }
    with (output / 'supplement_manifest.json').open('x') as stream:
        stream.write(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root, args.output)
    print(json.dumps({'output': str(args.output), 'restored_verified': result['restored_verified'],
                      'databases_integrity_checked': len(result['databases_integrity_checked']),
                      'complete_repository_or_secret_clearance': False}))


if __name__ == '__main__':
    main()
