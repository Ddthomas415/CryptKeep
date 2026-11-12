"""Local selected-evidence bundles; no provider, secret-file or service access."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import time

from services.control.group_a_systemd_policy import render_group_a_policy
from storage.sqlite_backup import copy_connection

MANIFEST = 'bundle.json'
_CHUNK = 1 << 20
_MAX_MANIFEST = 64 << 20
_CONFIG = {
    'strategy_runner': {'enabled','venue','symbols','strategy_preset','signal_source',
        'loop_interval_sec','qty','order_type','position_aware','sell_full_position',
        'min_bars','max_bars','use_ccxt_fallback','max_tick_age_sec','allow_first_signal_trade'},
    'paper_trading': {'enabled','quote_currency','starting_cash_quote','fee_bps','slippage_bps',
        'use_ccxt_fallback','max_order_qty','require_fresh_hourly_candles',
        'require_fresh_snapshot_quotes','default_venue','default_symbol','loop_interval_sec'},
    'execution': {'live_enabled'}, 'live_execution': {'armed'},
}
_BOOL = {'enabled','position_aware','sell_full_position','use_ccxt_fallback','allow_first_signal_trade',
         'require_fresh_hourly_candles','require_fresh_snapshot_quotes','live_enabled','armed'}


class BundleError(ValueError):
    """Fixed diagnostics; source contents and exception strings are not exposed."""


@dataclass(frozen=True)
class BundleLimits:
    max_files: int
    max_total_bytes: int
    max_file_bytes: int

    def __post_init__(self):
        if (any(type(n) is not int for n in (self.max_files,self.max_total_bytes,self.max_file_bytes))
                or not 1 <= self.max_files <= 100000
                or not 0 < self.max_file_bytes <= self.max_total_bytes < 2**63):
            raise BundleError('invalid_bundle_limits')


@dataclass(frozen=True)
class SQLiteSource:
    relative_path: str
    source: sqlite3.Connection


@dataclass(frozen=True)
class FileSource:
    relative_path: str
    stream: object
    size: int
    sha256: str


@dataclass(frozen=True)
class BundleReceipt:
    directory: Path
    manifest_sha256: str
    file_count: int
    total_bytes: int
    local_verified: bool = True
    offsite_verified: bool = False
    atomic_across_databases: bool = False
    selection_scope: str = 'explicit_inputs_only'


def _budget(deadline, clock):
    if type(deadline) not in (int,float) or not math.isfinite(deadline) or clock() >= deadline:
        raise BundleError('bundle_deadline')


def _sha(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}',value) is None:
        raise BundleError('invalid_manifest_identity')
    return value


def _accounts(release):
    policy = render_group_a_policy(release)
    prefix = policy.target.removesuffix('.target')+'-'
    return {u.removeprefix(prefix).removesuffix('-strategy.service') for u in policy.services
            if u.endswith('-strategy.service')}


def _path(name, kind, accounts):
    if (type(name) is not str or len(name)>512 or re.fullmatch('[A-Za-z0-9_./-]+',name) is None
            or str(PurePosixPath(name)) != name):
        raise BundleError('invalid_bundle_path')
    parts=PurePosixPath(name).parts
    if (not 1 <= len(parts) <= 16 or any(p.startswith('.') or p in ('..','.') for p in parts)
            or PurePosixPath(name).is_absolute()
            or any(word in name.lower() for word in ('credential','password','secret','browser-access-token'))):
        raise BundleError('invalid_bundle_path')
    if kind=='metadata' and name=='run_manifest.public.json':
        return name
    if not parts or parts[0] not in accounts:
        raise BundleError('invalid_bundle_path')
    if kind=='public_config' and parts[1:]==('runtime','config','user.public.json'):
        return name
    if len(parts)<3 or parts[1]!='data' or name.endswith(('-wal','-shm','-journal','.lock','.tmp')):
        raise BundleError('invalid_bundle_path')
    suffix=PurePosixPath(name).suffix
    if ((kind=='sqlite' and suffix not in ('.sqlite','.sqlite3','.db'))
            or (kind=='artifact' and suffix not in ('.json','.jsonl','.bin','.gz','.xz','.csv'))
            or kind not in ('sqlite','artifact')):
        raise BundleError('invalid_bundle_path')
    return name


def _private(path):
    path=Path(path)
    info=path.lstat()
    if (not path.is_absolute() or path.resolve(strict=True)!=path or not stat.S_ISDIR(info.st_mode)
            or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o700):
        raise BundleError('unsafe_bundle_directory')
    return path


def _new_directory(parent, prefix, identity):
    if type(identity) is not str or re.fullmatch('[a-z0-9]{8,40}',identity) is None:
        raise BundleError('invalid_bundle_identity')
    parent=_private(parent)
    result=parent/(prefix+identity)
    result.mkdir(mode=0o700,exist_ok=False)
    return _private(result)


def _new_file(path):
    missing=[]
    parent=path.parent
    while not parent.exists():
        missing.append(parent)
        parent=parent.parent
    _private(parent)
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        _private(directory)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    return os.fdopen(fd,'wb')


def _reader(path):
    if path.resolve(strict=True)!=path:
        raise BundleError('unsafe_bundle_file')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.geteuid()
                or stat.S_IMODE(info.st_mode)!=0o600):
            raise BundleError('unsafe_bundle_file')
        return os.fdopen(fd,'rb')
    except BaseException:
        os.close(fd)
        raise


def _sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _bytes_file(path, raw):
    with _new_file(path) as stream:
        if stream.write(raw)!=len(raw):
            raise BundleError('short_bundle_write')
        stream.flush()
        os.fsync(stream.fileno())


def _json(raw):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:
                raise BundleError('duplicate_manifest_key')
            result[key]=value
        return result
    def constant(_):
        raise BundleError('invalid_manifest_number')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=constant)


def _encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _public_config(value):
    if type(value) is not dict or any(type(k) is not str for k in value) or not set(value)<=set(_CONFIG):
        raise BundleError('invalid_public_configuration')
    result={}
    for group,fields in value.items():
        if type(fields) is not dict or any(type(k) is not str for k in fields) or not set(fields)<=_CONFIG[group]:
            raise BundleError('invalid_public_configuration')
        result[group]={}
        for key,item in fields.items():
            valid=False
            if key in _BOOL:
                valid=type(item) is bool
            elif key in ('venue','default_venue'):
                valid=type(item) is str and item=='coinbase'
            elif key=='quote_currency':
                valid=type(item) is str and item=='USD'
            elif key=='symbols':
                valid=type(item) is list and len(item)==1 and type(item[0]) is str and item[0] in ('BTC/USD','ETH/USD','SOL/USD')
            elif key=='default_symbol':
                valid=type(item) is str and item in ('BTC/USD','ETH/USD','SOL/USD')
            elif key=='strategy_preset':
                valid=type(item) is str and item in ('breakout_default','ema_cross_default','mean_reversion_default')
            elif key=='signal_source':
                valid=type(item) is str and item=='public_ohlcv_1h'
            elif key=='order_type':
                valid=type(item) is str and item in ('market','limit')
            else:
                valid=type(item) in (int,float) and math.isfinite(item) and abs(item)<=1e18
            if not valid:
                raise BundleError('invalid_public_configuration')
            result[group][key]=item
    return _encode(result)


def _run_metadata(value,release):
    allowed={'release','source_sha256','configuration_sha256','dependency_lock_sha256'}
    if (type(value) is not dict or not {'release','source_sha256'}<=set(value)<=allowed
            or value['release']!=release):
        raise BundleError('invalid_public_run_manifest')
    for key,item in value.items():
        if key!='release':
            _sha(item)
    return _encode(value)


def _copy_stream(source,destination,*,size,digest,deadline,clock):
    count=0
    hashed=hashlib.sha256()
    with _new_file(destination) as output:
        while True:
            _budget(deadline,clock)
            chunk=source.read(min(_CHUNK,size-count+1))
            if type(chunk) is not bytes or len(chunk)>min(_CHUNK,size-count+1):
                raise BundleError('invalid_artifact_stream')
            if not chunk:
                break
            count+=len(chunk)
            if count>size or output.write(chunk)!=len(chunk):
                raise BundleError('artifact_length_changed')
            hashed.update(chunk)
        if count!=size or hashed.hexdigest()!=digest:
            raise BundleError('artifact_identity_changed')
        output.flush()
        os.fsync(output.fileno())


def _file_hash(path,*,limit,deadline,clock):
    hashed=hashlib.sha256()
    count=0
    with _reader(path) as source:
        while True:
            _budget(deadline,clock)
            chunk=source.read(_CHUNK)
            if not chunk:
                break
            count+=len(chunk)
            if count>limit:
                raise BundleError('bundle_size_limit')
            hashed.update(chunk)
    return count,hashed.hexdigest()


def _sqlite_integrity(path,deadline,clock):
    with _reader(path) as source:
        header=source.read(20)
        if header[:16]!=b'SQLite format 3\x00' or header[18:20]!=b'\x01\x01':
            raise BundleError('non_standalone_sqlite_copy')
    con=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=0)
    try:
        con.set_progress_handler(lambda:int(clock()>=deadline),1000)
        con.execute('PRAGMA query_only=ON')
        con.execute('PRAGMA trusted_schema=OFF')
        if con.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
            raise BundleError('bundle_sqlite_integrity_failed')
        _budget(deadline,clock)
    finally:
        con.close()


def _sync_artifact_directories(root,names,deadline,clock):
    directories={root}
    for name in names:
        directories.update(root/p for p in PurePosixPath(name).parents if str(p)!='.')
    for path in sorted(directories,key=lambda p:len(p.parts),reverse=True):
        _budget(deadline,clock)
        _private(path)
        _sync_directory(path)


def create_bundle(parent,*,release,bundle_id,databases,artifacts,public_configurations,
                  public_run_manifest,limits,deadline,clock=time.monotonic):
    """Copy explicit trusted sources, not an inferred complete live inventory.

    Caller supplies attributed query-only connections and frozen streams and
    keeps a trusted private output parent free of hostile same-UID mutations.
    Failures preserve partial output; the manifest is written last. No source
    handle is closed, no source setting changed, no network/client action.
    """
    try:
        _budget(deadline,clock)
        if type(limits) is not BundleLimits or type(databases) not in (list,tuple) or type(artifacts) not in (list,tuple):
            raise BundleError('invalid_bundle_input')
        accounts=_accounts(release)
        if type(public_configurations) is not dict or not set(public_configurations)<=accounts:
            raise BundleError('invalid_public_configuration')
        if len(databases)+len(artifacts)+len(public_configurations)+1>limits.max_files:
            raise BundleError('bundle_file_limit')
        if len({id(item.source) for item in databases if type(item) is SQLiteSource})!=len(databases):
            raise BundleError('aliased_or_invalid_source_connection')
        public=[('run_manifest.public.json',_run_metadata(public_run_manifest,release),'metadata')]
        public += [(account+'/runtime/config/user.public.json',_public_config(cfg),'public_config')
                   for account,cfg in sorted(public_configurations.items())]
        paths=[]
        for item in databases:
            _budget(deadline,clock)
            if (type(item) is not SQLiteSource or type(item.source) is not sqlite3.Connection
                    or item.source.in_transaction or item.source.row_factory is not None
                    or item.source.execute('PRAGMA query_only').fetchone()!=(1,)):
                raise BundleError('invalid_source_connection')
            paths.append(_path(item.relative_path,'sqlite',accounts))
        for item in artifacts:
            _budget(deadline,clock)
            if (type(item) is not FileSource or type(item.size) is not int
                    or not 0<=item.size<=limits.max_file_bytes):
                raise BundleError('invalid_artifact_input')
            _sha(item.sha256)
            paths.append(_path(item.relative_path,'artifact',accounts))
        paths += [name for name,_,_ in public]
        names=set(paths)
        if (len(paths)>limits.max_files or len(names)!=len(paths)
                or any(str(parent) in names for name in names for parent in PurePosixPath(name).parents if str(parent)!='.')):
            raise BundleError('duplicate_or_aliased_bundle_path')
        _budget(deadline,clock)
        root=_new_directory(parent,'backup-',bundle_id)
        entries=[]
        total=0
        def add(name,kind):
            nonlocal total
            size,digest=_file_hash(root/name,limit=limits.max_file_bytes,deadline=deadline,clock=clock)
            total+=size
            if total>limits.max_total_bytes:
                raise BundleError('bundle_size_limit')
            entries.append({'path':name,'kind':kind,'bytes':size,'sha256':digest,
                'completed_utc':datetime.now(timezone.utc).isoformat()})
        for item in databases:
            _budget(deadline,clock)
            path=root/item.relative_path
            with _new_file(path) as held:
                con=sqlite3.connect(path,timeout=0)
                try:
                    copy_connection(item.source,con,deadline=deadline,
                        max_bytes=min(limits.max_file_bytes,limits.max_total_bytes-total),clock=clock)
                finally:
                    con.close()
                os.fsync(held.fileno())
            add(item.relative_path,'sqlite')
        for item in artifacts:
            if item.size>limits.max_total_bytes-total:
                raise BundleError('bundle_size_limit')
            _copy_stream(item.stream,root/item.relative_path,size=item.size,digest=item.sha256,
                deadline=deadline,clock=clock)
            add(item.relative_path,'artifact')
        for name,raw,kind in public:
            if len(raw)>min(limits.max_file_bytes,limits.max_total_bytes-total):
                raise BundleError('bundle_size_limit')
            _bytes_file(root/name,raw)
            add(name,kind)
        raw=_encode({'format':1,'release':release,'selection_scope':'explicit_inputs_only',
            'atomic_across_databases':False,'offsite_verified':False,'files':entries})
        if len(raw)>_MAX_MANIFEST or total+len(raw)>limits.max_total_bytes:
            raise BundleError('bundle_size_limit')
        _sync_artifact_directories(root,paths,deadline,clock)
        _budget(deadline,clock)
        _bytes_file(root/MANIFEST,raw)
        _sync_directory(root)
        _sync_directory(root.parent)
        return verify_bundle(root,expected_manifest_sha256=hashlib.sha256(raw).hexdigest(),
            limits=limits,deadline=deadline,clock=clock)
    except BundleError:
        raise
    except Exception:
        raise BundleError('bundle_creation_failed_or_commit_uncertain') from None


def _load(root,expected,limits,deadline,clock):
    _budget(deadline,clock)
    if type(limits) is not BundleLimits:
        raise BundleError('invalid_bundle_limits')
    root=_private(root)
    _sha(expected)
    with _reader(root/MANIFEST) as source:
        raw=source.read(min(_MAX_MANIFEST,limits.max_total_bytes)+1)
    if len(raw)>min(_MAX_MANIFEST,limits.max_total_bytes) or hashlib.sha256(raw).hexdigest()!=expected:
        raise BundleError('manifest_identity_changed')
    value=_json(raw)
    if (type(value) is not dict or set(value)!={'format','release','selection_scope','atomic_across_databases','offsite_verified','files'}
            or type(value['format']) is not int or value['format']!=1
            or value['selection_scope']!='explicit_inputs_only'
            or value['atomic_across_databases'] is not False or value['offsite_verified'] is not False
            or type(value['files']) is not list or not 1<=len(value['files'])<=limits.max_files):
        raise BundleError('invalid_manifest_schema')
    accounts=_accounts(value['release'])
    seen=set()
    total=len(raw)
    for item in value['files']:
        _budget(deadline,clock)
        if (type(item) is not dict or set(item)!={'path','kind','bytes','sha256','completed_utc'}
                or type(item['bytes']) is not int or not 0<=item['bytes']<=limits.max_file_bytes):
            raise BundleError('invalid_manifest_entry')
        name=_path(item['path'],item['kind'],accounts)
        if name in seen:
            raise BundleError('duplicate_manifest_path')
        seen.add(name)
        _sha(item['sha256'])
        if type(item['completed_utc']) is not str or len(item['completed_utc'])>64 or datetime.fromisoformat(item['completed_utc']).utcoffset() is None:
            raise BundleError('invalid_manifest_timestamp')
        total+=item['bytes']
    if total>limits.max_total_bytes or 'run_manifest.public.json' not in seen:
        raise BundleError('bundle_size_or_scope_invalid')
    return root,raw,value,total


def _inventory(root,names,deadline,clock):
    directories={str(p) for n in names for p in PurePosixPath(n).parents if str(p)!='.'}
    seen=set()
    pending=[root]
    while pending:
        directory=pending.pop()
        _private(directory)
        with os.scandir(directory) as entries:
            for entry in entries:
                _budget(deadline,clock)
                path=Path(entry.path)
                rel=path.relative_to(root).as_posix()
                if entry.is_dir(follow_symlinks=False) and rel in directories:
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False) and rel in names:
                    seen.add(rel)
                else:
                    raise BundleError('unexpected_bundle_entry')
    if seen!=names:
        raise BundleError('missing_bundle_entry')


def verify_bundle(directory,*,expected_manifest_sha256,limits,deadline,clock=time.monotonic):
    """Verify against an external manifest hash, never the bundle's own claim."""
    try:
        root,raw,value,total=_load(directory,expected_manifest_sha256,limits,deadline,clock)
        _inventory(root,{MANIFEST,*(item['path'] for item in value['files'])},deadline,clock)
        for item in value['files']:
            size,digest=_file_hash(root/item['path'],limit=limits.max_file_bytes,deadline=deadline,clock=clock)
            if size!=item['bytes'] or digest!=item['sha256']:
                raise BundleError('bundle_file_identity_changed')
            if item['kind']=='sqlite':
                _sqlite_integrity(root/item['path'],deadline,clock)
            elif item['kind'] in ('public_config','metadata'):
                with _reader(root/item['path']) as source:
                    content=source.read(min(limits.max_file_bytes,1<<20)+1)
                if len(content)>min(limits.max_file_bytes,1<<20):
                    raise BundleError('public_metadata_size_limit')
                parsed=_json(content)
                canonical=(_public_config(parsed) if item['kind']=='public_config'
                           else _run_metadata(parsed,value['release']))
                if canonical!=content:
                    raise BundleError('public_metadata_not_canonical')
        _budget(deadline,clock)
        return BundleReceipt(root,expected_manifest_sha256,len(value['files']),total)
    except BundleError:
        raise
    except Exception:
        raise BundleError('bundle_verification_failed') from None


def restore_to_new(directory,parent,*,restore_id,expected_manifest_sha256,limits,deadline,
                   clock=time.monotonic):
    """Restore selected copies to a new private directory, never active state."""
    try:
        receipt=verify_bundle(directory,expected_manifest_sha256=expected_manifest_sha256,
            limits=limits,deadline=deadline,clock=clock)
        root,raw,value,_=_load(receipt.directory,expected_manifest_sha256,limits,deadline,clock)
        target=_new_directory(parent,'restore-',restore_id)
        for item in value['files']:
            with _reader(root/item['path']) as source:
                _copy_stream(source,target/item['path'],size=item['bytes'],digest=item['sha256'],
                    deadline=deadline,clock=clock)
        _sync_artifact_directories(target,[item['path'] for item in value['files']],deadline,clock)
        _budget(deadline,clock)
        _bytes_file(target/MANIFEST,raw)
        _sync_directory(target)
        _sync_directory(target.parent)
        return verify_bundle(target,expected_manifest_sha256=expected_manifest_sha256,
            limits=limits,deadline=deadline,clock=clock)
    except BundleError:
        raise
    except Exception:
        raise BundleError('bundle_restore_failed_or_commit_uncertain') from None
