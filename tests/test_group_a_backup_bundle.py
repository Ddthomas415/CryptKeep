"""Real temporary SQLite/WAL and byte artifacts; no accounts or provider calls."""
from contextlib import ExitStack
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import os
import threading

import pytest

from services.control import group_a_backup_bundle as backup
from services.control.group_a_systemd_policy import render_group_a_policy

R='frozen42'


@pytest.fixture
def sources(tmp_path):
    with ExitStack() as stack:
        dbs=[]
        files=[]
        configs={}
        prefix=f'cbp-group-a-{R}-'
        accounts=[u.removeprefix(prefix).removesuffix('-strategy.service')
                  for u in render_group_a_policy(R).services if u.endswith('-strategy.service')]
        for account in accounts:
            path=tmp_path/(account+'.sqlite')
            writer=sqlite3.connect(path)
            stack.callback(writer.close)
            writer.execute('PRAGMA journal_mode=WAL')
            writer.execute('CREATE TABLE positions(symbol TEXT, cash_cents INTEGER)')
            writer.execute('INSERT INTO positions VALUES (?,?)',(account.rsplit('-',1)[1],100001))
            writer.commit()
            reader=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
            stack.callback(reader.close)
            reader.execute('PRAGMA query_only=ON')
            dbs.append(backup.SQLiteSource(account+'/data/paper_trading.sqlite',reader))
            raw=b'{"kind":"SYNTHETIC decision","action":"hold"}\n'
            files.append(backup.FileSource(account+'/data/runner_decisions/session.jsonl',
                io.BytesIO(raw),len(raw),hashlib.sha256(raw).hexdigest()))
            configs[account]={'strategy_runner':{'enabled':True,'qty':.01},
                              'paper_trading':{'fee_bps':50},'execution':{'live_enabled':False}}
        parent=tmp_path/'output'
        parent.mkdir(mode=0o700)
        yield dict(parent=parent,dbs=dbs,files=files,configs=configs,accounts=accounts)


def limits(**kwargs):
    return backup.BundleLimits(max_files=100,max_total_bytes=10_000_000,
        max_file_bytes=1_000_000,**kwargs)


def create(sources,**kwargs):
    return backup.create_bundle(sources['parent'],release=R,bundle_id='batch0001',
        databases=sources['dbs'],artifacts=sources['files'],
        public_configurations=kwargs.pop('public_configurations',sources['configs']),
        public_run_manifest={'release':R,'source_sha256':'a'*64},
        limits=kwargs.pop('limits',limits()),deadline=kwargs.pop('deadline',backup.time.monotonic()+10),
        **kwargs)


def test_nine_account_wal_artifact_config_round_trip_is_exact_and_local_only(sources):
    result=create(sources)
    assert result.local_verified is True and result.offsite_verified is False
    assert result.atomic_across_databases is False
    assert result.selection_scope=='explicit_inputs_only'
    assert result.file_count==28
    verified=backup.verify_bundle(result.directory,expected_manifest_sha256=result.manifest_sha256,
        limits=limits(),deadline=backup.time.monotonic()+10)
    assert verified==result
    restored=backup.restore_to_new(result.directory,sources['parent'],restore_id='restore01',
        expected_manifest_sha256=result.manifest_sha256,limits=limits(),deadline=backup.time.monotonic()+10)
    assert restored.directory != result.directory and restored.manifest_sha256==result.manifest_sha256
    for account in sources['accounts']:
        name=account+'/data/paper_trading.sqlite'
        assert (restored.directory/name).read_bytes()==(result.directory/name).read_bytes()
        with sqlite3.connect((restored.directory/name).as_uri()+'?mode=ro',uri=True) as con:
            assert con.execute('SELECT cash_cents FROM positions').fetchone()==(100001,)
        config=json.loads((restored.directory/account/'runtime/config/user.public.json').read_bytes())
        assert config['execution']['live_enabled'] is False
    assert all(s.source.execute('PRAGMA query_only').fetchone()==(1,) for s in sources['dbs'])
    assert not list(result.directory.rglob('*-wal'))


def test_existing_bundle_or_restore_is_never_overwritten(sources):
    first=create(sources)
    marker=(first.directory/'keep')
    marker.write_bytes(b'preserve')
    with pytest.raises(backup.BundleError):
        create(sources)
    assert marker.read_bytes()==b'preserve'


def test_existing_restore_directory_is_never_modified(sources):
    result=create(sources)
    existing=sources['parent']/'restore-restore01'
    existing.mkdir(mode=0o700)
    (existing/'keep').write_bytes(b'preserve')
    with pytest.raises(backup.BundleError):
        backup.restore_to_new(result.directory,sources['parent'],restore_id='restore01',
            expected_manifest_sha256=result.manifest_sha256,limits=limits(),deadline=backup.time.monotonic()+10)
    assert (existing/'keep').read_bytes()==b'preserve'


@pytest.mark.parametrize('path',['../secret','/etc/passwd','.env','x/data/.env.local',
    'breakout-default-btc/runtime/config/user.yaml','breakout-default-btc/data/x/../secret',
    'breakout-default-btc/data/x-wal','breakout-default-btc/data/x.lock',
    'breakout-default-btc/data/credentials.json','other-account/data/evidence.json'])
def test_private_or_escaping_paths_refused_before_stream_read(sources,path):
    class Trap:
        def read(self,*args):
            pytest.fail('must not read rejected source')
    sources['files']=[backup.FileSource(path,Trap(),1,'a'*64)]
    with pytest.raises(backup.BundleError):
        create(sources)
    assert list(sources['parent'].iterdir())==[]


def test_duplicate_or_file_directory_prefix_collision_refused(sources):
    sources['files'].append(sources['files'][0])
    with pytest.raises(backup.BundleError):
        create(sources)
    assert list(sources['parent'].iterdir())==[]


def test_file_directory_prefix_collision_refused_before_output(sources):
    first=sources['files'][0]
    sources['files'].append(backup.FileSource(first.relative_path+'/nested.json',io.BytesIO(b''),0,
        hashlib.sha256(b'').hexdigest()))
    with pytest.raises(backup.BundleError):
        create(sources)
    assert list(sources['parent'].iterdir())==[]


def test_artifact_hash_or_length_change_preserves_partial_without_manifest(sources):
    item=sources['files'][0]
    sources['files'][0]=backup.FileSource(item.relative_path,io.BytesIO(b'UNIQUE-SECRET-PAYLOAD'),item.size,item.sha256)
    with pytest.raises(backup.BundleError) as error:
        create(sources)
    assert 'UNIQUE-SECRET-PAYLOAD' not in str(error.value)
    assert (sources['parent']/'backup-batch0001').is_dir()
    assert not (sources['parent']/'backup-batch0001'/backup.MANIFEST).exists()


def test_tampered_file_or_manifest_prevents_restore_before_destination_creation(sources):
    result=create(sources)
    path=result.directory/sources['files'][0].relative_path
    path.write_bytes(b'tampered')
    with pytest.raises(backup.BundleError):
        backup.restore_to_new(result.directory,sources['parent'],restore_id='restore01',
            expected_manifest_sha256=result.manifest_sha256,limits=limits(),deadline=backup.time.monotonic()+10)
    assert not (sources['parent']/'restore-restore01').exists()


def test_manifest_and_content_cannot_self_authorize_an_edited_backup(sources):
    result=create(sources)
    manifest=result.directory/backup.MANIFEST
    value=json.loads(manifest.read_bytes())
    value['release']='frozen43'
    manifest.write_text(json.dumps(value))
    with pytest.raises(backup.BundleError,match='manifest'):
        backup.verify_bundle(result.directory,expected_manifest_sha256=result.manifest_sha256,
            limits=limits(),deadline=backup.time.monotonic()+10)


@pytest.mark.parametrize('extra',['unexpected.txt','.env','another.sqlite-wal'])
def test_unregistered_files_are_not_treated_as_a_verified_bundle(sources,extra):
    result=create(sources)
    (result.directory/extra).write_bytes(b'UNREAD private-extra')
    with pytest.raises(backup.BundleError):
        backup.verify_bundle(result.directory,expected_manifest_sha256=result.manifest_sha256,
            limits=limits(),deadline=backup.time.monotonic()+10)


def test_symlink_and_hardlinked_copy_are_rejected(sources):
    result=create(sources)
    path=result.directory/sources['files'][0].relative_path
    path.unlink()
    path.symlink_to(sources['parent']/'not-a-source')
    with pytest.raises(backup.BundleError):
        backup.verify_bundle(result.directory,expected_manifest_sha256=result.manifest_sha256,
            limits=limits(),deadline=backup.time.monotonic()+10)


def test_hardlinked_copy_is_rejected(sources):
    result=create(sources)
    path=result.directory/sources['files'][0].relative_path
    os.link(path,sources['parent']/'outside-link')
    with pytest.raises(backup.BundleError):
        backup.verify_bundle(result.directory,expected_manifest_sha256=result.manifest_sha256,
            limits=limits(),deadline=backup.time.monotonic()+10)


def test_unknown_or_secret_config_is_refused_not_copied(sources):
    config={sources['accounts'][0]:{'alerts':{'slack_webhook_url':'SYNTHETIC-hidden-secret'}}}
    with pytest.raises(backup.BundleError) as error:
        create(sources,public_configurations=config)
    assert 'hidden-secret' not in str(error.value)
    assert list(sources['parent'].iterdir())==[]


@pytest.mark.parametrize('value',[True,0,-1,float('inf'),float('nan')])
def test_invalid_limits_refused(value):
    with pytest.raises(backup.BundleError):
        backup.BundleLimits(max_files=value,max_total_bytes=10000,max_file_bytes=1000)


def test_expired_or_tiny_budget_cannot_publish_a_completion_manifest(sources):
    with pytest.raises(backup.BundleError):
        create(sources,deadline=backup.time.monotonic()-1)
    assert list(sources['parent'].iterdir())==[]
    with pytest.raises(backup.BundleError):
        create(sources,limits=backup.BundleLimits(max_files=100,max_total_bytes=1000,max_file_bytes=1000))
    assert not list(sources['parent'].rglob(backup.MANIFEST))


def test_source_connection_must_already_be_query_only_and_idle(sources):
    sources['dbs'][0].source.execute('PRAGMA query_only=OFF')
    with pytest.raises(backup.BundleError):
        create(sources)
    assert sources['dbs'][0].source.execute('PRAGMA query_only').fetchone()==(0,)
    assert not list(sources['parent'].rglob(backup.MANIFEST))


def test_same_connection_cannot_silently_represent_two_database_sources(sources):
    second=sources['dbs'][1]
    sources['dbs'][1]=backup.SQLiteSource(second.relative_path,sources['dbs'][0].source)
    with pytest.raises(backup.BundleError,match='source_connection'):
        create(sources)
    assert list(sources['parent'].iterdir())==[]


def test_fsync_failure_is_not_reported_as_completed_and_partial_files_remain(sources,monkeypatch):
    monkeypatch.setattr(backup.os,'fsync',lambda *_:(_ for _ in ()).throw(OSError('SYNTHETIC-secret')))
    with pytest.raises(backup.BundleError) as error:
        create(sources)
    assert 'secret' not in str(error.value)
    assert (sources['parent']/'backup-batch0001').exists()


def test_private_output_parent_symlink_or_permissions_are_refused(sources,tmp_path):
    alias=tmp_path/'alias'
    alias.symlink_to(sources['parent'],target_is_directory=True)
    sources['parent']=alias
    with pytest.raises(backup.BundleError):
        create(sources)


def test_permissive_output_parent_is_refused(sources):
    sources['parent'].chmod(0o755)
    with pytest.raises(backup.BundleError):
        create(sources)
    assert list(sources['parent'].iterdir())==[]


def test_artifact_extra_byte_and_bad_digest_do_not_complete(sources):
    first=sources['files'][0]
    sources['files'][0]=backup.FileSource(first.relative_path,io.BytesIO(b'x'),0,hashlib.sha256(b'').hexdigest())
    with pytest.raises(backup.BundleError):
        create(sources)
    assert not list(sources['parent'].rglob(backup.MANIFEST))


def test_source_write_transaction_is_refused_without_rolling_it_back(sources):
    connection=sqlite3.connect(':memory:')
    try:
        connection.execute('CREATE TABLE t(x)')
        connection.execute('INSERT INTO t VALUES (1)')
        sources['dbs'][0]=backup.SQLiteSource(sources['dbs'][0].relative_path,connection)
        with pytest.raises(backup.BundleError):
            create(sources)
        assert connection.in_transaction is True
        assert connection.execute('SELECT x FROM t').fetchone()==(1,)
    finally:
        connection.close()


def test_new_copy_api_remains_consistent_under_a_real_concurrent_wal_writer(sources):
    reader=sources['dbs'][0].source
    path=reader.execute('PRAGMA database_list').fetchone()[2]
    stop=threading.Event()
    started=threading.Event()
    def writer():
        with sqlite3.connect(path) as con:
            con.execute('CREATE TABLE totals(a INTEGER,b INTEGER)')
            con.execute('INSERT INTO totals VALUES(100,900)')
            con.commit()
            started.set()
            while not stop.is_set():
                con.execute('UPDATE totals SET a=a+1,b=b-1')
                con.commit()
    thread=threading.Thread(target=writer)
    thread.start()
    assert started.wait(3)
    try:
        result=create(sources)
    finally:
        stop.set()
        thread.join(timeout=3)
    assert not thread.is_alive()
    with sqlite3.connect((result.directory/sources['dbs'][0].relative_path).as_uri()+'?mode=ro',uri=True) as con:
        assert con.execute('SELECT a+b FROM totals').fetchone()==(1000,)


def test_failure_after_manifest_creation_reports_uncertainty_not_a_receipt(sources,monkeypatch):
    fsync=backup.os.fsync
    def fail_after_publish(fd):
        if (sources['parent']/'backup-batch0001'/backup.MANIFEST).exists():
            raise OSError('SYNTHETIC-private failure')
        fsync(fd)
    monkeypatch.setattr(backup.os,'fsync',fail_after_publish)
    with pytest.raises(backup.BundleError) as error:
        create(sources)
    assert 'uncertain' in str(error.value)
    assert 'private' not in str(error.value)
    assert (sources['parent']/'backup-batch0001'/backup.MANIFEST).exists()


def test_every_created_directory_is_private_and_synced_before_manifest(sources,monkeypatch):
    synced=[]
    sync=backup._sync_directory
    def observe(path):
        synced.append((path,(sources['parent']/'backup-batch0001'/backup.MANIFEST).exists()))
        sync(path)
    monkeypatch.setattr(backup,'_sync_directory',observe)
    result=create(sources)
    directories={p for p in result.directory.rglob('*') if p.is_dir()}
    assert all(p.stat().st_mode&0o777==0o700 for p in directories)
    assert directories <= {p for p,manifest_exists in synced if not manifest_exists}


def test_configuration_numeric_boolean_and_unknown_fields_are_not_accepted(sources):
    cfg={sources['accounts'][0]:{'execution':{'live_enabled':0}}}
    with pytest.raises(backup.BundleError):
        create(sources,public_configurations=cfg)
    assert list(sources['parent'].iterdir())==[]


def test_restore_rechecks_source_bytes_after_initial_verification(sources,monkeypatch):
    result=create(sources)
    original=backup._new_directory
    def change_after_verified(*args):
        target=original(*args)
        (result.directory/sources['files'][0].relative_path).write_bytes(b'changed-after-verification')
        return target
    monkeypatch.setattr(backup,'_new_directory',change_after_verified)
    with pytest.raises(backup.BundleError):
        backup.restore_to_new(result.directory,sources['parent'],restore_id='restore01',
            expected_manifest_sha256=result.manifest_sha256,limits=limits(),deadline=backup.time.monotonic()+10)
    assert not (sources['parent']/'restore-restore01'/backup.MANIFEST).exists()


@pytest.mark.parametrize('mutate',[
    lambda x:x.update(format=True), lambda x:x.update(offsite_verified=0),
    lambda x:x.update(atomic_across_databases=0),lambda x:x.update(extra='SYNTHETIC-secret'),
    lambda x:x['files'][0].update(bytes=True),lambda x:x['files'][0].update(path='../outside'),
    lambda x:x['files'][0].update(kind='unsupported'),
    lambda x:x['files'][0].update(completed_utc='2026-11-11T00:00:00'),
    lambda x:x['files'].append(x['files'][0]),
])
def test_externally_pinned_but_malformed_manifest_is_still_refused(sources,mutate):
    result=create(sources)
    path=result.directory/backup.MANIFEST
    value=json.loads(path.read_bytes())
    mutate(value)
    raw=json.dumps(value).encode()
    path.write_bytes(raw)
    with pytest.raises(backup.BundleError) as error:
        backup.verify_bundle(result.directory,expected_manifest_sha256=hashlib.sha256(raw).hexdigest(),
            limits=limits(),deadline=backup.time.monotonic()+10)
    assert 'SYNTHETIC-secret' not in str(error.value)


@pytest.mark.parametrize('raw',[b'{"format":1,"format":1}',b'{"x":NaN}',b'['*1200+b']'*1200])
def test_duplicate_nonfinite_or_deep_manifest_is_refused(sources,raw):
    result=create(sources)
    (result.directory/backup.MANIFEST).write_bytes(raw)
    with pytest.raises(backup.BundleError):
        backup.verify_bundle(result.directory,expected_manifest_sha256=hashlib.sha256(raw).hexdigest(),
            limits=limits(),deadline=backup.time.monotonic()+10)


def test_final_metadata_validation_cannot_return_success_after_deadline(sources,monkeypatch):
    result=create(sources)
    now=[0.0]
    validated=[0]
    original=backup._public_config
    def expire_after_validation(*args):
        value=original(*args)
        validated[0]+=1
        if validated[0]==len(sources['configs']):
            now[0]=11.0
        return value
    monkeypatch.setattr(backup,'_public_config',expire_after_validation)
    with pytest.raises(backup.BundleError,match='deadline'):
        backup.verify_bundle(result.directory,expected_manifest_sha256=result.manifest_sha256,
            limits=limits(),deadline=10.0,clock=lambda:now[0])
