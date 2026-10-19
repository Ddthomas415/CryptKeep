"""Disposable synthetic recovery fixtures only; never use user credentials."""
import io
import json
from pathlib import Path
import sqlite3
import tarfile
import zipfile

import pytest

from scripts.research import build_recovery_copy as recovery


def source(tmp_path, files):
    root = tmp_path / 'repo'
    root.mkdir()
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


def test_restore_preserves_bytes_quoted_names_and_executable_bit(tmp_path):
    files = {'scripts/data/tool.py': b'print(1)\n', 'space "quote".md': b'evidence\n'}
    root = source(tmp_path, files)
    (root / 'scripts/data/tool.py').chmod(0o755)
    out = tmp_path / 'copy'
    report = recovery.build(root, out, list(files))
    assert report['restored_files_verified'] == 2 and report['exclusions'] == []
    for rel, data in files.items():
        assert (out / 'restored' / rel).read_bytes() == data
        assert (root / rel).read_bytes() == data
    assert (out / 'restored/scripts/data/tool.py').stat().st_mode & 0o100
    assert not report['complete_repository_or_secret_clearance']


@pytest.mark.parametrize('rel', ['.env', 'config/user.yaml', '.aws/credentials',
                                 'phase1_research_copilot/.browser-access-token',
                                 '.cbp_state/private.json', 'config/private.env'])
def test_denied_paths_not_opened(tmp_path, monkeypatch, rel):
    root = source(tmp_path, {rel: b'do-not-read'})
    monkeypatch.setattr(recovery, 'read_regular', lambda *a: pytest.fail('credential path opened'))
    out = tmp_path / 'copy'
    report = recovery.build(root, out, [rel])
    assert report['exclusions'] == [{'path': rel, 'reason': 'credential_or_runtime_path'}]
    assert not (out / 'files' / rel).exists()


def test_secret_values_not_persisted_or_returned(tmp_path):
    secret = b'ghp_' + b'Z' * 30
    root = source(tmp_path, {'unsafe.txt': secret, 'safe.py': b'pass\n'})
    out = tmp_path / 'copy'
    report = recovery.build(root, out, ['unsafe.txt', 'safe.py'])
    assert report['restored_files_verified'] == 1
    assert secret.decode() not in json.dumps(report)
    for p in out.rglob('*'):
        if p.is_file():
            assert secret not in p.read_bytes()


@pytest.mark.parametrize('member', ['../escape', '/absolute', '.env'])
def test_unsafe_nested_archive_excluded(tmp_path, member):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        item = tarfile.TarInfo(member)
        item.size = 4
        archive.addfile(item, io.BytesIO(b'safe'))
    root = source(tmp_path, {'raw.tar.gz': buffer.getvalue()})
    report = recovery.build(root, tmp_path / 'copy', ['raw.tar.gz'])
    assert report['exclusions'] and report['restored_files_verified'] == 0


def test_nested_zip_secret_is_not_treated_as_clean(tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('sheet.xml', b'github_pat_' + b'X' * 30)
    root = source(tmp_path, {'report.xlsx': buffer.getvalue()})
    report = recovery.build(root, tmp_path / 'copy', ['report.xlsx'])
    assert report['restored_files_verified'] == 0 and report['exclusions']


def test_symlink_and_symlink_ancestor_not_followed(tmp_path):
    root = source(tmp_path, {'safe': b'safe'})
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'secret').write_bytes(b'not-for-copy')
    (root / 'link').symlink_to(outside, target_is_directory=True)
    (root / 'leaf').symlink_to(outside / 'secret')
    report = recovery.build(root, tmp_path / 'copy', ['link/secret', 'leaf'])
    assert report['restored_files_verified'] == 0 and len(report['exclusions']) == 2


def test_existing_destination_and_repo_destination_refused(tmp_path):
    root = source(tmp_path, {'safe': b'safe'})
    existing = tmp_path / 'existing'
    existing.mkdir()
    with pytest.raises(FileExistsError):
        recovery.build(root, existing, ['safe'])
    with pytest.raises(ValueError, match='outside_repo'):
        recovery.build(root, root / 'copy', ['safe'])


def test_public_database_copy_integrity_without_source_sql(tmp_path):
    root = source(tmp_path, {})
    with sqlite3.connect(root / 'public.sqlite') as connection:
        connection.execute('CREATE TABLE prices (price REAL)')
        connection.execute('INSERT INTO prices VALUES (12.0)')
    before = (root / 'public.sqlite').read_bytes()
    report = recovery.build(root, tmp_path / 'copy', ['public.sqlite'])
    assert report['restored_databases_checked'] == ['public.sqlite']
    assert (root / 'public.sqlite').read_bytes() == before


def test_database_with_journal_deferred(tmp_path):
    root = source(tmp_path, {'public.sqlite': b'unread', 'public.sqlite-wal': b'active'})
    report = recovery.build(root, tmp_path / 'copy', ['public.sqlite'])
    assert report['exclusions'][0]['reason'] == 'database_journal_present'


def test_source_change_prevents_success_receipt(tmp_path, monkeypatch):
    root = source(tmp_path, {'safe.py': b'pass\n'})
    original, calls = recovery.read_regular, []
    def read(*args):
        calls.append(1)
        if len(calls) == 2:
            (root / 'safe.py').write_bytes(b'changed\n')
        return original(*args)
    monkeypatch.setattr(recovery, 'read_regular', read)
    out = tmp_path / 'copy'
    with pytest.raises(ValueError, match='source_changed_before_seal'):
        recovery.build(root, out, ['safe.py'])
    assert not (out / 'backup_manifest.json').exists()


def test_restore_rejects_archive_link(tmp_path):
    path = tmp_path / 'bad.tar.gz'
    with tarfile.open(path, 'w:gz') as archive:
        member = tarfile.TarInfo('safe')
        member.type = tarfile.SYMTYPE
        member.linkname = '../escape'
        archive.addfile(member)
    with pytest.raises(ValueError, match='restore_member_refused'):
        recovery.restore_verified(path, tmp_path / 'restored', [{'path': 'safe', 'bytes': 0, 'sha256': 'x'}])


def test_inventory_adds_only_explicit_public_companion_and_database_paths(tmp_path, monkeypatch):
    from types import SimpleNamespace

    approved = 'phase1_research_copilot/news_ingestion/main.py'
    database = sorted(recovery.PUBLIC_DATABASES)[0]
    private = 'phase1_research_copilot/config/credentials.json'
    fifth = 'research/not-approved/public_archive.sqlite'
    root = source(tmp_path, {approved: b'pass', database: b'public', private: b'unread', fifth: b'unread'})
    monkeypatch.setattr(recovery.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        stdout=('safe.py\0' + private + '\0' + fifth + '\0').encode()))
    selected = recovery.inventory(root)
    assert selected == sorted(['safe.py', approved, database])
    actual_read = recovery.read_regular
    def read(root_, rel):
        assert rel not in (private, fifth)
        return actual_read(root_, rel)
    monkeypatch.setattr(recovery, 'read_regular', read)
    report = recovery.build(root, tmp_path / 'copy', [private, fifth, approved])
    assert report['restored_files_verified'] == 1 and len(report['exclusions']) == 2


@pytest.mark.parametrize('suffix', ['.tar', '.txt', '.bin'])
def test_archive_content_not_outer_suffix_controls_screening(suffix):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        member = tarfile.TarInfo('.env')
        member.size = 15
        archive.addfile(member, io.BytesIO(b'synthetic-only!'))
    assert recovery.screened_reason(buffer.getvalue(), 'bundle' + suffix) == 'archive_member_refused'


def test_safe_plaintext_and_safe_mislabeled_tar_controls():
    assert recovery.screened_reason(b'public notes\n', 'notes.txt') is None
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        member = tarfile.TarInfo('candles.json')
        member.size = 2
        archive.addfile(member, io.BytesIO(b'[]'))
    assert recovery.screened_reason(buffer.getvalue(), 'raw.txt') is None


@pytest.mark.parametrize('root_name', ['.', './'])
def test_normal_tar_root_directory_does_not_crash_or_bypass_members(root_name):
    for payload_name, accepted in [('public.json', True), ('.env', False)]:
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w') as archive:
            root = tarfile.TarInfo(root_name)
            root.type = tarfile.DIRTYPE
            archive.addfile(root)
            item = tarfile.TarInfo(payload_name)
            item.size = 2
            archive.addfile(item, io.BytesIO(b'[]'))
        reason = recovery.screened_reason(buffer.getvalue(), 'archive.txt')
        assert (reason is None) == accepted


def test_regular_root_member_is_refused_not_skipped():
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        item = tarfile.TarInfo('.')
        item.size = 2
        archive.addfile(item, io.BytesIO(b'[]'))
    assert recovery.screened_reason(buffer.getvalue(), 'archive.tar') == 'archive_unreadable'
    with pytest.raises(ValueError, match='unsafe_relative_path'):
        recovery.safe_rel('.')


def test_zip_root_directory_does_not_skip_credential_member():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('./', '')
        archive.writestr('.env', 'synthetic')
    assert recovery.screened_reason(buffer.getvalue(), 'archive.zip') == 'archive_member_refused'


@pytest.mark.parametrize('mode,payload', [(0o120777, b'target'), (0o100600, b''),
                                         (0o40700, b'payload')])
def test_zip_root_name_is_not_enough_to_skip_type_or_payload(mode, payload):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        member = zipfile.ZipInfo('./')
        member.create_system = 3
        member.external_attr = mode << 16
        archive.writestr(member, payload)
    assert recovery.screened_reason(buffer.getvalue(), 'archive.zip') == 'archive_member_refused'


def test_empty_typed_zip_root_directory_is_allowed():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        member = zipfile.ZipInfo('./')
        member.create_system = 3
        member.external_attr = 0o40700 << 16
        archive.writestr(member, '')
        archive.writestr('public.json', '[]')
    assert recovery.screened_reason(buffer.getvalue(), 'archive.zip') is None


def test_tar_root_directory_payload_is_refused():
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        member = tarfile.TarInfo('.')
        member.type, member.size = tarfile.DIRTYPE, 7
        archive.addfile(member, io.BytesIO(b'payload'))
    assert recovery.screened_reason(buffer.getvalue(), 'archive.tar') == 'archive_member_refused'


def test_nonroot_directory_payload_is_not_skipped():
    zipped, packed = io.BytesIO(), io.BytesIO()
    with zipfile.ZipFile(zipped, 'w') as archive:
        archive.writestr('folder/', b'payload')
    with tarfile.open(fileobj=packed, mode='w') as archive:
        member = tarfile.TarInfo('folder')
        member.type, member.size = tarfile.DIRTYPE, 7
        archive.addfile(member, io.BytesIO(b'payload'))
    assert recovery.screened_reason(zipped.getvalue(), 'archive.zip') == 'archive_member_refused'
    assert recovery.screened_reason(packed.getvalue(), 'archive.tar') == 'archive_member_refused'
