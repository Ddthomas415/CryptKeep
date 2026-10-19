"""Synthetic fixtures for named-asset preservation, no live credentials/data."""
from contextlib import closing
import io
import json
import sqlite3
import tarfile

import pytest

from scripts.research import preserve_recovery_exclusions as recovery


def make_tar(files, links=()):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:xz') as archive:
        for name, data in files:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        for name in links:
            member = tarfile.TarInfo(name)
            member.type, member.linkname = tarfile.SYMTYPE, '../outside'
            archive.addfile(member)
    return buffer.getvalue()


def public_db(tmp_path, monkeypatch):
    root = tmp_path / 'source'
    root.mkdir()
    rel = 'research/study/public_archive.sqlite'
    path = root / rel
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE prices (value INTEGER)')
        db.execute('INSERT INTO prices VALUES (42)')
        db.commit()
        db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    monkeypatch.setattr(recovery.base, 'PUBLIC_DATABASES', {rel})
    return root, rel, path


def test_stable_empty_wal_database_recovery_never_opens_source_sql(tmp_path, monkeypatch):
    root, rel, path = public_db(tmp_path, monkeypatch)
    (root / (rel + '-wal')).write_bytes(b'')
    (root / (rel + '-shm')).write_bytes(b'untouched shared memory')
    before = {p.name: p.read_bytes() for p in path.parent.iterdir()}
    monkeypatch.setattr(recovery, 'ARCHIVES', {})
    connect = sqlite3.connect
    def guarded(database, *args, **kwargs):
        assert str(root) not in str(database), 'SQL opened original database'
        return connect(database, *args, **kwargs)
    monkeypatch.setattr(recovery.sqlite3, 'connect', guarded)
    out = tmp_path / 'result'
    result = recovery.build(root, out)
    assert result['restored_verified'] == 1
    assert result['databases_integrity_checked'] == [rel]
    assert {p.name: p.read_bytes() for p in path.parent.iterdir()} == before
    assert (out / 'restored' / rel).read_bytes() == path.read_bytes()
    assert not (out / 'restored' / (rel + '-shm')).exists()


@pytest.mark.parametrize('tail,value', [('-wal', b'committed WAL'), ('-journal', b'')])
def test_active_or_rollback_journal_refused(tmp_path, monkeypatch, tail, value):
    root, rel, _ = public_db(tmp_path, monkeypatch)
    (root / (rel + tail)).write_bytes(value)
    with pytest.raises(ValueError, match='wal_requires|rollback_journal'):
        recovery.stable_database(root, rel)


def test_wal_change_during_copy_refused(tmp_path, monkeypatch):
    root, rel, path = public_db(tmp_path, monkeypatch)
    (root / (rel + '-wal')).write_bytes(b'')
    read = recovery.base.read_regular
    def changing(root, name):
        data = read(root, name)
        if name == rel:
            (path.parent / (path.name + '-wal')).write_bytes(b'new transaction')
        return data
    monkeypatch.setattr(recovery.base, 'read_regular', changing)
    with pytest.raises(ValueError, match='nonempty_wal'):
        recovery.stable_database(root, rel)


def test_source_symlink_and_unknown_database_refused(tmp_path, monkeypatch):
    root, rel, path = public_db(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='outside_named_scope'):
        recovery.stable_database(root, 'research/other/public_archive.sqlite')
    (root / (rel + '-wal')).symlink_to(path)
    with pytest.raises(OSError):
        recovery.stable_database(root, rel)


def test_public_progress_exception_is_exact_and_not_global():
    source, name = next(iter(recovery.LOGS))
    data = recovery.LOGS[source, name]
    assert recovery.member_screen(data, name, source) == 'exact_public_progress_log'
    with pytest.raises(ValueError, match='progress_log_changed'):
        recovery.member_screen(data + b'extra', name, source)
    with pytest.raises(ValueError, match='archive_member_refused'):
        recovery.member_screen(data, name, 'other.tar.xz')


def test_slug_exception_requires_pinned_bytes_and_exclusive_pattern(monkeypatch):
    name = 'cmc/weekly/test.json'
    token = 'sk-' + 'Z' * 28
    data = json.dumps([[1, 'SKHYx', token, 4, 5, 6, 7, 8, 'date', []]]).encode()
    monkeypatch.setattr(recovery, 'CMC_SLUG_FILES', {name: recovery.digest(data)})
    source = recovery.RAW + 'cmc_weekly_and_trending.tar.xz'
    assert recovery.member_screen(data, name, source) == 'pinned_public_coin_slug'
    with pytest.raises(ValueError, match='pinned_cmc_member_changed'):
        recovery.member_screen(data + b' ', name, source)
    bad = json.dumps([[1, 'SKHYx', token, 4, 5, 6, 7, 8, 'ghp_' + 'X' * 30, []]]).encode()
    monkeypatch.setattr(recovery, 'CMC_SLUG_FILES', {name: recovery.digest(bad)})
    with pytest.raises(ValueError, match='not_exclusive'):
        recovery.member_screen(bad, name, source)


@pytest.mark.parametrize('files,links', [([('../escape', b'x')], []),
    ([('.env', b'x')], []), ([('data', b'one'), ('data', b'two')], []),
    ([], ['link']), ([('data.json', b'ghp_' + b'X' * 30)], [])])
def test_archive_unsafe_members_still_refused(monkeypatch, files, links):
    data = make_tar(files, links)
    monkeypatch.setattr(recovery, 'ARCHIVES', {'fixture': recovery.digest(data)})
    with pytest.raises(ValueError):
        recovery.inspect_archive(data, 'fixture')


def test_archive_frozen_hash_and_public_control(monkeypatch):
    data = make_tar([('data.json', b'{"public":true}')])
    monkeypatch.setattr(recovery, 'ARCHIVES', {'fixture': recovery.digest(data)})
    assert recovery.inspect_archive(data, 'fixture')['members'] == 1
    with pytest.raises(ValueError, match='hash_mismatch'):
        recovery.inspect_archive(data + b'changed', 'fixture')


def test_existing_output_and_internal_destination_refused(tmp_path, monkeypatch):
    root, _, _ = public_db(tmp_path, monkeypatch)
    existing = tmp_path / 'existing'
    existing.mkdir()
    with pytest.raises(FileExistsError):
        recovery.build(root, existing)
    with pytest.raises(ValueError, match='external_directory'):
        recovery.build(root, root / 'copy')


def test_mutation_before_seal_leaves_no_success_manifest(tmp_path, monkeypatch):
    root, rel, _ = public_db(tmp_path, monkeypatch)
    monkeypatch.setattr(recovery, 'ARCHIVES', {})
    stable = recovery.stable_database
    calls = []
    def changing(*args):
        calls.append(1)
        data, state = stable(*args)
        if len(calls) > 1:
            state['changed'] = True
        return data, state
    monkeypatch.setattr(recovery, 'stable_database', changing)
    out = tmp_path / 'copy'
    with pytest.raises(ValueError, match='state_changed_before_seal'):
        recovery.build(root, out)
    assert not (out / 'supplement_manifest.json').exists()
