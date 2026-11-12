"""Acquire declared, quiescent account-data trees for the local backup core.

No implicit state-root lookup, database opening, YAML reading or provider action.
Caller-owned query-only connections require trusted creation/path provenance:
database_list attributes a pathname, not the inode held by an old connection.
Source namespaces must be trusted; this is not hostile same-UID race isolation.
"""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile
import time

from services.control import group_a_backup_bundle as core

_REQUIRED = {'paper_trading.sqlite', 'intent_queue.sqlite', 'strategy_state.sqlite'}
_SIDECARS = ('-wal', '-shm', '-journal')
_CHUNK = 1 << 20
_JSON_LIMIT = 4 << 20
_ARTIFACT = re.compile(
    r'(?:signal_inputs/[0-9a-f]{64}\.json|'
    r'runner_(?:decisions|candle_diagnostics)/[0-9a-f]{64}/[0-9a-f]{32}\.jsonl)'
)
_ARTIFACT_DIRECTORY = re.compile(
    r'(?:signal_inputs|runner_(?:decisions|candle_diagnostics)(?:/[0-9a-f]{64})?)'
)


@dataclass(frozen=True)
class AccountSource:
    account: str
    data_directory: Path
    databases: tuple[core.SQLiteSource, ...]


@dataclass(frozen=True)
class AcquisitionReceipt:
    bundle: core.BundleReceipt
    account_count: int
    artifact_inventory_sha256: str
    sources_revalidated: bool = True
    source_scope: str = 'declared_account_data_with_local_objects'


def _directory(path):
    if not isinstance(path, Path) or not path.is_absolute() or path.resolve(strict=True) != path:
        raise core.BundleError('unsafe_source_directory')
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise core.BundleError('unsafe_source_directory')
    return path


def _signature(info, kind):
    base = (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)
    return base + ((info.st_size, info.st_mtime_ns, info.st_ctime_ns) if kind == 'artifact' else ())


def _inventory(accounts, limits, deadline, clock):
    result = {}
    directories = set()
    total = 0
    count = 0
    roster = {a.account for a in accounts}
    for account in accounts:
        root = _directory(account.data_directory)
        pending = [root]
        while pending:
            directory = _directory(pending.pop())
            core._budget(deadline, clock)
            identity = directory.lstat()
            key = (identity.st_dev, identity.st_ino)
            if key in directories:
                raise core.BundleError('aliased_source_directory')
            directories.add(key)
            rel = directory.relative_to(root).as_posix()
            name = account.account + '/data' + ('' if rel == '.' else '/' + rel)
            result[name] = ('directory', _signature(identity, 'directory'))
            with os.scandir(directory) as entries:
                for entry in entries:
                    core._budget(deadline, clock)
                    count += 1
                    if count > limits.max_files * 4:
                        raise core.BundleError('source_inventory_limit')
                    path = Path(entry.path)
                    relative = path.relative_to(root).as_posix()
                    name = account.account + '/data/' + relative
                    info = entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        core._path(name + '/probe.json', 'artifact', roster)
                        if _ARTIFACT_DIRECTORY.fullmatch(relative) is None:
                            raise core.BundleError('unrecognized_artifact_path')
                        pending.append(path)
                        continue
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                        raise core.BundleError('unsafe_source_file')
                    suffix = next((s for s in _SIDECARS if name.endswith(s)), None)
                    kind = ('sidecar' if suffix else
                            'sqlite' if path.suffix in ('.sqlite', '.sqlite3', '.db') else 'artifact')
                    # Extensions do not authorize reading arbitrary config/credential JSON.
                    if kind == 'artifact' and _ARTIFACT.fullmatch(relative) is None:
                        raise core.BundleError('unrecognized_artifact_path')
                    # Reuse the accepted bundle's path policy; sidecars are metadata only.
                    core._path(name[:-len(suffix)] if suffix else name,
                               'sqlite' if kind == 'sidecar' else kind, roster)
                    result[name] = (kind, _signature(info, kind))
                    if kind != 'sidecar':
                        if info.st_size > limits.max_file_bytes:
                            raise core.BundleError('source_file_size_limit')
                        total += info.st_size
                        if total > limits.max_total_bytes:
                            raise core.BundleError('source_total_size_limit')
    for name, (kind, _) in result.items():
        if kind == 'sidecar':
            suffix = next(s for s in _SIDECARS if name.endswith(s))
            if result.get(name[:-len(suffix)], (None,))[0] != 'sqlite':
                raise core.BundleError('orphan_sqlite_sidecar')
    if sum(kind not in ('directory', 'sidecar') for kind, _ in result.values()) + len(accounts) + 1 > limits.max_files:
        raise core.BundleError('source_file_count_limit')
    core._budget(deadline, clock)
    return result


def _validate_connections(accounts, inventory, deadline, clock):
    declared = {}
    objects = set()
    stores = set()
    for account in accounts:
        prefix = account.account + '/data/'
        for item in account.databases:
            core._budget(deadline, clock)
            if type(item) is not core.SQLiteSource or item.relative_path in declared:
                raise core.BundleError('invalid_source_database_mapping')
            con = item.source
            if (not item.relative_path.startswith(prefix) or type(con) is not sqlite3.Connection
                    or id(con) in objects or con.in_transaction or con.row_factory is not None
                    or con.execute('PRAGMA query_only').fetchone() != (1,)):
                raise core.BundleError('invalid_source_database_mapping')
            evidence = inventory.get(item.relative_path)
            if evidence is None or evidence[0] != 'sqlite':
                raise core.BundleError('missing_source_database')
            path = account.data_directory / item.relative_path[len(prefix):]
            main = [row[2] for row in con.execute('PRAGMA database_list') if row[1] == 'main']
            if main != [str(path)]:
                raise core.BundleError('source_connection_path_mismatch')
            identity = evidence[1][:2]
            if identity in stores:
                raise core.BundleError('aliased_source_database')
            objects.add(id(con))
            stores.add(identity)
            declared[item.relative_path] = item
        if not {prefix + name for name in _REQUIRED} <= set(declared):
            raise core.BundleError('missing_required_account_store')
    if set(declared) != {name for name, (kind, _) in inventory.items() if kind == 'sqlite'}:
        raise core.BundleError('unmapped_source_database')
    return list(declared.values())


def _read_source(path, expected, deadline, clock, output=None):
    core._budget(deadline, clock)
    if path.resolve(strict=True) != path:
        raise core.BundleError('source_path_changed')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or _signature(info, 'artifact') != expected:
            raise core.BundleError('source_file_changed')
        size = info.st_size
        digest = hashlib.sha256()
        remaining = size
        first = True
        while remaining:
            core._budget(deadline, clock)
            raw = source.read(min(_CHUNK, remaining))
            if not raw:
                raise core.BundleError('source_file_truncated')
            if first and raw.startswith(b'SQLite format 3\x00'):
                raise core.BundleError('unmapped_sqlite_artifact')
            first = False
            digest.update(raw)
            if output is not None and output.write(raw) != len(raw):
                raise core.BundleError('short_acquisition_write')
            remaining -= len(raw)
        if source.read(1) or _signature(os.fstat(source.fileno()), 'artifact') != expected:
            raise core.BundleError('source_file_changed')
    if _signature(path.lstat(), 'artifact') != expected:
        raise core.BundleError('source_path_changed')
    core._budget(deadline, clock)
    return size, digest.hexdigest()


class _Slice:
    def __init__(self, spool, offset, size):
        self.spool, self.offset, self.remaining = spool, offset, size

    def read(self, count):
        self.spool.seek(self.offset)
        raw = self.spool.read(min(count, self.remaining))
        self.offset += len(raw)
        self.remaining -= len(raw)
        return raw


def _record_coverage(spool, frozen, deadline, clock):
    checked_prefixes = set()
    def object_info(account, digest):
        core._budget(deadline, clock)
        core._sha(digest)
        name = account + '/data/signal_inputs/' + digest + '.json'
        if name not in frozen or frozen[name][2] != digest:
            raise core.BundleError('missing_or_changed_recording_object')
        return frozen[name]
    def object_bytes(account, digest):
        offset, size, _ = object_info(account, digest)
        if size > _JSON_LIMIT:
            raise core.BundleError('recording_object_parse_limit')
        core._budget(deadline, clock)
        spool.seek(offset)
        return spool.read(size)
    for name, (offset, size, digest) in frozen.items():
        core._budget(deadline, clock)
        account, _, rel = name.split('/', 2)
        if rel.startswith('signal_inputs/'):
            if name.rsplit('/', 1)[-1] != digest + '.json':
                raise core.BundleError('recording_object_identity_changed')
        if not rel.startswith('runner_decisions/'):
            continue
        used = 0
        while used < size:
            core._budget(deadline, clock)
            spool.seek(offset + used)
            line = spool.readline(min(_JSON_LIMIT, size - used) + 1)
            if len(line) > min(_JSON_LIMIT, size - used) or not line.endswith(b'\n'):
                raise core.BundleError('partial_or_oversized_decision_record')
            used += len(line)
            value = core._json(line)
            if type(value) is not dict or set(value) != {'sha256', 'payload'} or type(value['payload']) is not dict:
                raise core.BundleError('unsupported_decision_record')
            payload = value['payload']
            if value['sha256'] != hashlib.sha256(core._encode(payload)).hexdigest():
                raise core.BundleError('decision_record_identity_changed')
            if payload.get('object_scope') != 'local':
                raise core.BundleError('external_recording_objects_not_acquired')
            for key in ('code_sha256', 'settings_sha256'):
                object_info(account, payload.get(key))
            digest = payload.get('completed_prefix_sha256')
            object_info(account, digest)
            if (account, digest) in checked_prefixes:
                continue
            prefix = core._json(object_bytes(account, digest))
            if (type(prefix) is not dict or prefix.get('type') != 'completed_prefix'
                    or type(prefix.get('bar_refs')) is not list or len(prefix['bar_refs']) > len(frozen)):
                raise core.BundleError('invalid_completed_prefix')
            for ref in prefix['bar_refs']:
                object_info(account, ref)
            checked_prefixes.add((account, digest))
    core._budget(deadline, clock)


def acquire_bundle(parent, *, release, bundle_id, accounts, public_configurations,
                   public_run_manifest, limits, deadline, clock=time.monotonic):
    """Return only after selected roots and artifact bytes are revalidated.

    Artifacts must be quiescent throughout acquisition. Active append, rotation
    or shared/outside-root recording references refuse rather than disappear.
    A post-copy failure retains the local bundle but issues no acquisition
    receipt. This is not complete operating configuration or R10 attestation.
    """
    try:
        core._budget(deadline, clock)
        if type(limits) is not core.BundleLimits or type(accounts) not in (tuple, list):
            raise core.BundleError('invalid_acquisition_input')
        roster = core._accounts(release)
        if (len(accounts) != len(roster) or any(type(a) is not AccountSource for a in accounts)
                or {a.account for a in accounts} != roster
                or any(type(a.databases) not in (tuple, list) for a in accounts)
                or type(public_configurations) is not dict or set(public_configurations) != roster):
            raise core.BundleError('incomplete_account_roster')
        for config in public_configurations.values():
            core._public_config(config)
        core._run_metadata(public_run_manifest, release)
        parent = core._private(parent)
        roots = [_directory(a.data_directory) for a in accounts]
        if any(parent.is_relative_to(root) or root.is_relative_to(parent) for root in roots):
            raise core.BundleError('output_source_overlap')
        if any(left.is_relative_to(right) or right.is_relative_to(left)
               for i, left in enumerate(roots) for right in roots[i + 1:]):
            raise core.BundleError('overlapping_account_roots')
        inventory = _inventory(accounts, limits, deadline, clock)
        databases = _validate_connections(accounts, inventory, deadline, clock)
        sources = {a.account: a.data_directory for a in accounts}
        frozen = {}
        with tempfile.TemporaryFile(mode='w+b', dir=parent) as spool:
            for name, (kind, signature) in sorted(inventory.items()):
                if kind != 'artifact':
                    continue
                account, _, rel = name.split('/', 2)
                offset = spool.tell()
                size, digest = _read_source(sources[account] / rel, signature, deadline, clock, spool)
                frozen[name] = (offset, size, digest)
            _record_coverage(spool, frozen, deadline, clock)
            streams = [core.FileSource(name, _Slice(spool, offset, size), size, digest)
                       for name, (offset, size, digest) in frozen.items()]
            receipt = core.create_bundle(parent, release=release, bundle_id=bundle_id,
                databases=databases, artifacts=streams, public_configurations=public_configurations,
                public_run_manifest=public_run_manifest, limits=limits, deadline=deadline, clock=clock)
            if _inventory(accounts, limits, deadline, clock) != inventory:
                raise core.BundleError('source_inventory_changed_after_copy')
            _validate_connections(accounts, inventory, deadline, clock)
            for name, (_, size, digest) in frozen.items():
                account, _, rel = name.split('/', 2)
                if _read_source(sources[account] / rel, inventory[name][1], deadline, clock) != (size, digest):
                    raise core.BundleError('source_bytes_changed_after_copy')
            if _inventory(accounts, limits, deadline, clock) != inventory:
                raise core.BundleError('source_inventory_changed_during_revalidation')
            core._budget(deadline, clock)
            identity = hashlib.sha256(core._encode({name: [size, digest]
                for name, (_, size, digest) in frozen.items()})).hexdigest()
            core._budget(deadline, clock)
            return AcquisitionReceipt(receipt, len(accounts), identity)
    except core.BundleError:
        raise
    except Exception:
        raise core.BundleError('source_acquisition_failed_or_output_uncertain') from None
