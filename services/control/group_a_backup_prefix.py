"""Explicit local/shared recording-prefix acquisition, never an operating job.

Reuse the recorder's advisory lock protocol and the accepted local bundle core.
Source content/provenance and private namespaces remain trusted; an inode held
by an old caller SQLite connection is not attested by pathname comparisons.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile
import time

from services.control import group_a_backup_acquisition as strict
from services.control import group_a_backup_bundle as core

_CHUNK = 1 << 20
_JSON_LIMIT = 4 << 20
_CAS_NAME = re.compile(r'[0-9a-f]{64}\.json')
_PUBLICATION_TEMP = re.compile(r'\.capture-[a-z0-9_]{8}')
_NOTE = 'recording_prefixes.json'


@dataclass(frozen=True)
class JournalCutoff:
    relative_path: str
    size: int
    sha256: str
    captured_utc: str


@dataclass(frozen=True)
class PrefixReceipt:
    bundle: core.BundleReceipt
    cutoffs: tuple[JournalCutoff, ...]
    capture_scope: str = 'per_file_complete_prefix'
    new_sessions: str = 'excluded_after_initial_inventory'
    atomic_across_files: bool = False


@contextmanager
def _locked_journal(path, expected, deadline, clock):
    core._budget(deadline, clock)
    if path.resolve(strict=True) != path:
        raise core.BundleError('journal_path_changed')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as source:
        try:
            fcntl.flock(source.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            raise core.BundleError('journal_writer_busy') from None
        info = os.fstat(source.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or strict._signature(info, 'directory') != expected[:5]):
            raise core.BundleError('journal_identity_changed')
        core._budget(deadline, clock)
        yield source, info
        if strict._signature(path.lstat(), 'directory') != expected[:5]:
            raise core.BundleError('journal_path_changed')
    core._budget(deadline, clock)


def _copy_prefix(source, size, deadline, clock, output=None):
    digest = hashlib.sha256()
    remaining = size
    while remaining:
        core._budget(deadline, clock)
        raw = source.read(min(remaining, _CHUNK))
        if not raw:
            raise core.BundleError('journal_prefix_truncated')
        digest.update(raw)
        if output is not None and output.write(raw) != len(raw):
            raise core.BundleError('short_prefix_write')
        remaining -= len(raw)
    core._budget(deadline, clock)
    return digest.hexdigest()


def _freeze_journal(path, expected, output, *, deadline, clock, max_bytes):
    # Only copying is inside the lock; parse/reference resolution runs later.
    with _locked_journal(path, expected, deadline, clock) as (source, info):
        size = info.st_size
        if size > max_bytes:
            raise core.BundleError('journal_prefix_size_limit')
        if size and os.pread(source.fileno(), 1, size - 1) != b'\n':
            raise core.BundleError('partial_initial_journal_tail')
        captured = datetime.now(timezone.utc).isoformat()
        digest = _copy_prefix(source, size, deadline, clock, output)
        if strict._signature(os.fstat(source.fileno()), 'artifact') != strict._signature(info, 'artifact'):
            raise core.BundleError('journal_changed_during_locked_copy')
    return size, digest, captured


def _verify_prefix(path, expected, cutoff, deadline, clock):
    with _locked_journal(path, expected, deadline, clock) as (source, info):
        if info.st_size < cutoff.size:
            raise core.BundleError('journal_prefix_truncated')
        if _copy_prefix(source, cutoff.size, deadline, clock) != cutoff.sha256:
            raise core.BundleError('journal_prefix_changed')
        # A later incomplete append is outside this cutoff, not a repair target.


def _shared_inventory(roots, max_entries, deadline, clock):
    found = {}
    count = 0
    for root in sorted(set(roots)):
        strict._directory(root)
        entries = {}
        with os.scandir(root) as stream:
            for entry in stream:
                core._budget(deadline, clock)
                count += 1
                if count > max_entries:
                    raise core.BundleError('shared_inventory_limit')
                info = entry.stat(follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode):
                    raise core.BundleError('unsafe_shared_object')
                if _PUBLICATION_TEMP.fullmatch(entry.name):
                    if info.st_nlink not in (1, 2):
                        raise core.BundleError('unsafe_publication_temporary')
                    continue  # Metadata only, never a payload source.
                if _CAS_NAME.fullmatch(entry.name) is None or info.st_nlink != 1:
                    raise core.BundleError('unrecognized_or_linked_shared_object')
                entries[entry.name[:-5]] = strict._signature(info, 'artifact')
        found[root] = entries
    core._budget(deadline, clock)
    return found


class _Stage:
    def __init__(self, spool, limits, roster, base_count, deadline, clock):
        self.spool, self.limits, self.roster = spool, limits, roster
        self.base_count, self.deadline, self.clock = base_count, deadline, clock
        self.files = {}
        self.sources = {}
        self.used_bytes = 0

    def room(self, name, size):
        core._budget(self.deadline, self.clock)
        core._path(name, 'artifact', self.roster)
        if (name in self.files or len(self.files) + self.base_count + 1 > self.limits.max_files
                or not 0 <= size <= self.limits.max_file_bytes
                or self.used_bytes + size > self.limits.max_total_bytes):
            raise core.BundleError('prefix_bundle_budget_or_collision')

    def remember(self, name, offset, size, digest):
        self.files[name] = (offset, size, digest)
        self.used_bytes += size

    def object(self, path, name, digest, expected=None):
        core._sha(digest)
        if path in self.sources:
            if name not in self.files:
                offset, size, actual = self.files[self.sources[path][2]]
                self.room(name, size)
                self.remember(name, offset, size, actual)
            return
        expected = expected or strict._signature(path.lstat(), 'artifact')
        if name in self.files:
            size, actual = strict._read_source(path, expected, self.deadline, self.clock)
        else:
            size = path.lstat().st_size
            self.room(name, size)
            self.spool.seek(0, os.SEEK_END)
            offset = self.spool.tell()
            size, actual = strict._read_source(path, expected, self.deadline, self.clock, self.spool)
            self.remember(name, offset, size, actual)
        if actual != digest:
            raise core.BundleError('recording_object_digest_changed')
        self.sources[path] = (expected, digest, name)

    def bytes(self, name, raw):
        self.room(name, len(raw))
        self.spool.seek(0, os.SEEK_END)
        offset = self.spool.tell()
        if self.spool.write(raw) != len(raw):
            raise core.BundleError('short_prefix_metadata_write')
        self.remember(name, offset, len(raw), hashlib.sha256(raw).hexdigest())


def _closure(stage, accounts, shared, shared_destination, cutoffs):
    account_roots = {a.account: a.data_directory for a in accounts}
    scopes = {c.relative_path: set() for c in cutoffs}
    checked_prefixes = set()
    def object_info(account, scope, digest):
        core._budget(stage.deadline, stage.clock)
        core._sha(digest)
        if scope == 'local':
            root = account_roots[account] / 'signal_inputs'
            name = account + '/data/signal_inputs/' + digest + '.json'
        elif scope == 'shared' and account in shared:
            root = shared[account]
            name = shared_destination + '/' + digest + '.json'
        else:
            raise core.BundleError('missing_explicit_object_mapping')
        strict._directory(root)
        stage.object(root / (digest + '.json'), name, digest)
        return stage.files[name]
    for cutoff in cutoffs:
        if '/data/runner_decisions/' not in cutoff.relative_path:
            continue
        account = cutoff.relative_path.split('/', 1)[0]
        offset, size, _ = stage.files[cutoff.relative_path]
        used = 0
        while used < size:
            core._budget(stage.deadline, stage.clock)
            stage.spool.seek(offset + used)
            line = stage.spool.readline(min(_JSON_LIMIT, size - used) + 1)
            if len(line) > min(_JSON_LIMIT, size - used) or not line.endswith(b'\n'):
                raise core.BundleError('invalid_prefix_record_length')
            used += len(line)
            envelope = core._json(line)
            if (type(envelope) is not dict or set(envelope) != {'sha256', 'payload'}
                    or type(envelope['payload']) is not dict):
                raise core.BundleError('unsupported_prefix_record')
            payload = envelope['payload']
            if envelope['sha256'] != hashlib.sha256(core._encode(payload)).hexdigest():
                raise core.BundleError('prefix_record_digest_changed')
            scope = payload.get('object_scope')
            for key in ('code_sha256', 'settings_sha256'):
                object_info(account, scope, payload.get(key))
            digest = payload.get('completed_prefix_sha256')
            object_offset, object_size, _ = object_info(account, scope, digest)
            scopes[cutoff.relative_path].add(scope)
            if (account, scope, digest) in checked_prefixes:
                continue
            if object_size > _JSON_LIMIT:
                raise core.BundleError('prefix_object_parse_limit')
            stage.spool.seek(object_offset)
            value = core._json(stage.spool.read(object_size))
            if (type(value) is not dict or value.get('type') != 'completed_prefix'
                    or type(value.get('bar_refs')) is not list or len(value['bar_refs']) > stage.limits.max_files):
                raise core.BundleError('invalid_recorded_prefix_object')
            for ref in value['bar_refs']:
                object_info(account, scope, ref)
            checked_prefixes.add((account, scope, digest))
    return scopes


def _check_inventory(initial, current):
    for name, (kind, signature) in initial.items():
        if kind == 'sidecar':
            continue
        actual = current.get(name)
        if actual is None or actual[0] != kind:
            raise core.BundleError('captured_source_disappeared')
        is_journal = '/data/runner_decisions/' in name or '/data/runner_candle_diagnostics/' in name
        if (signature[:5] != actual[1][:5] if is_journal else signature != actual[1]):
            raise core.BundleError('captured_source_identity_changed')


def acquire_prefix_bundle(parent, *, release, bundle_id, accounts, public_configurations,
                          public_run_manifest, limits, deadline, shared_object_roots=None,
                          clock=time.monotonic):
    """Capture initial sessions plus object closure, not a global atomic view.

    Local publication temp/link windows can conservatively refuse. New sessions
    after initial enumeration are excluded; each captured journal has its own
    complete byte cutoff. No source repair, retry, private config or provider I/O.
    """
    try:
        core._budget(deadline, clock)
        roster = core._accounts(release)
        shared = {} if shared_object_roots is None else shared_object_roots
        if (type(limits) is not core.BundleLimits or type(accounts) not in (list, tuple)
                or len(accounts) != len(roster) or any(type(a) is not strict.AccountSource for a in accounts)
                or {a.account for a in accounts} != roster
                or any(type(a.databases) not in (list, tuple) for a in accounts)
                or type(shared) is not dict or not set(shared) <= roster
                or type(public_configurations) is not dict or set(public_configurations) != roster):
            raise core.BundleError('invalid_prefix_acquisition_roster')
        for value in public_configurations.values():
            core._public_config(value)
        core._run_metadata(public_run_manifest, release)
        parent = core._private(parent)
        roots = [strict._directory(a.data_directory) for a in accounts]
        extra = [strict._directory(p) for p in shared.values()]
        unique = list(dict.fromkeys((*roots, *extra)))
        identities = [(p.lstat().st_dev, p.lstat().st_ino) for p in unique]
        if len(set(identities)) != len(unique):
            raise core.BundleError('aliased_prefix_source_root')
        if (any(parent.is_relative_to(p) or p.is_relative_to(parent) for p in unique)
                or any(a.is_relative_to(b) or b.is_relative_to(a)
                       for i, a in enumerate(unique) for b in unique[i + 1:])
                or len(set(roots)) != len(roots) or set(roots) & set(extra)):
            raise core.BundleError('overlapping_prefix_source_roots')
        root_identities = {p: strict._signature(p.lstat(), 'directory') for p in unique}
        inventory = strict._inventory(accounts, limits, deadline, clock)
        databases = strict._validate_connections(accounts, inventory, deadline, clock)
        shared_initial = _shared_inventory(extra, limits.max_files * 4 - len(inventory), deadline, clock)
        sources = {a.account: a.data_directory for a in accounts}
        shared_destination = sorted(roster)[0] + '/data/shared_signal_inputs'
        cutoffs = []
        with tempfile.TemporaryFile(mode='w+b', dir=parent) as spool:
            stage = _Stage(spool, limits, roster, len(databases) + len(accounts) + 1, deadline, clock)
            for name, (kind, signature) in sorted(inventory.items()):
                if kind != 'artifact':
                    continue
                account, _, rel = name.split('/', 2)
                path = sources[account] / rel
                if rel.startswith('signal_inputs/'):
                    stage.object(path, name, path.stem, signature)
                else:
                    stage.room(name, 0)
                    spool.seek(0, os.SEEK_END)
                    offset = spool.tell()
                    size, digest, captured = _freeze_journal(path, signature, spool, deadline=deadline,
                        clock=clock, max_bytes=min(limits.max_file_bytes, limits.max_total_bytes - stage.used_bytes))
                    stage.remember(name, offset, size, digest)
                    cutoffs.append(JournalCutoff(name, size, digest, captured))
            for root, objects in shared_initial.items():
                for digest, signature in objects.items():
                    stage.object(root / (digest + '.json'), shared_destination + '/' + digest + '.json', digest, signature)
            scopes = _closure(stage, accounts, shared, shared_destination, cutoffs)
            for account in sorted(roster):
                rows = [{'path': c.relative_path, 'bytes': c.size, 'sha256': c.sha256,
                         'captured_utc': c.captured_utc, 'scopes': sorted(scopes[c.relative_path])}
                        for c in cutoffs if c.relative_path.startswith(account + '/')]
                used_scopes = {scope for row in rows for scope in row['scopes']}
                directories = {scope: (account + '/data/signal_inputs' if scope == 'local' else shared_destination)
                               for scope in sorted(used_scopes)}
                raw = core._encode({'format': 1, 'scope': 'per_file_complete_prefix',
                    'new_sessions': 'excluded_after_initial_inventory', 'atomic_across_files': False,
                    'object_directories': directories, 'journals': rows})
                if len(raw) > _JSON_LIMIT:
                    raise core.BundleError('prefix_metadata_size_limit')
                stage.bytes(account + '/data/' + _NOTE, raw)
            streams = [core.FileSource(name, strict._Slice(spool, offset, size), size, digest)
                       for name, (offset, size, digest) in stage.files.items()]
            receipt = core.create_bundle(parent, release=release, bundle_id=bundle_id,
                databases=databases, artifacts=streams, public_configurations=public_configurations,
                public_run_manifest=public_run_manifest, limits=limits, deadline=deadline, clock=clock)
            current = strict._inventory(accounts, limits, deadline, clock)
            _check_inventory(inventory, current)
            strict._validate_connections(accounts, current, deadline, clock)
            _shared_inventory(extra, limits.max_files * 4 - len(current), deadline, clock)
            for path, (signature, digest, _) in stage.sources.items():
                if strict._read_source(path, signature, deadline, clock)[1] != digest:
                    raise core.BundleError('captured_object_changed')
            for cutoff in cutoffs:
                account, _, rel = cutoff.relative_path.split('/', 2)
                _verify_prefix(sources[account] / rel, inventory[cutoff.relative_path][1], cutoff, deadline, clock)
            for root, identity in root_identities.items():
                if strict._signature(strict._directory(root).lstat(), 'directory') != identity:
                    raise core.BundleError('prefix_root_changed')
            core._budget(deadline, clock)
            return PrefixReceipt(receipt, tuple(cutoffs))
    except core.BundleError:
        raise
    except Exception:
        raise core.BundleError('prefix_acquisition_failed_or_output_uncertain') from None


def restored_recording_directories(directory, *, account, journal_path,
                                   expected_manifest_sha256, limits, deadline, clock=time.monotonic):
    """Return scope destinations only from an externally hash-verified bundle."""
    try:
        receipt = core.verify_bundle(directory, expected_manifest_sha256=expected_manifest_sha256,
            limits=limits, deadline=deadline, clock=clock)
        _, _, manifest, _ = core._load(receipt.directory, expected_manifest_sha256, limits, deadline, clock)
        roster = core._accounts(manifest['release'])
        if type(account) is not str or account not in roster or type(journal_path) is not str:
            raise core.BundleError('invalid_restored_recording_identity')
        expected_shared = sorted(roster)[0] + '/data/shared_signal_inputs'
        with core._reader(receipt.directory / account / 'data' / _NOTE) as source:
            raw = source.read(min(limits.max_file_bytes, _JSON_LIMIT) + 1)
        if len(raw) > min(limits.max_file_bytes, _JSON_LIMIT):
            raise core.BundleError('prefix_metadata_size_limit')
        value = core._json(raw)
        if (type(value) is not dict or set(value) != {'format', 'scope', 'new_sessions',
                'atomic_across_files', 'object_directories', 'journals'} or type(value['format']) is not int
                or value['format'] != 1 or value['scope'] != 'per_file_complete_prefix'
                or value['new_sessions'] != 'excluded_after_initial_inventory'
                or value['atomic_across_files'] is not False or type(value['object_directories']) is not dict
                or type(value['journals']) is not list or len(value['journals']) > limits.max_files):
            raise core.BundleError('invalid_restored_prefix_metadata')
        directories = value['object_directories']
        if not set(directories) <= {'local', 'shared'} or any(
                path != (account + '/data/signal_inputs' if scope == 'local' else expected_shared)
                for scope, path in directories.items()):
            raise core.BundleError('invalid_restored_object_destination')
        indexed = {item['path']: item for item in manifest['files']}
        seen = set()
        selected = None
        for row in value['journals']:
            core._budget(deadline, clock)
            if (type(row) is not dict or set(row) != {'path', 'bytes', 'sha256', 'captured_utc', 'scopes'}
                    or type(row['path']) is not str or not row['path'].startswith(account + '/data/')
                    or strict._ARTIFACT.fullmatch(row['path'].split('/', 2)[2]) is None
                    or '/data/runner_' not in row['path'] or row['path'] in seen
                    or type(row['bytes']) is not int or type(row['scopes']) is not list
                    or any(type(s) is not str or s not in directories for s in row['scopes'])
                    or len(set(row['scopes'])) != len(row['scopes'])
                    or type(row['captured_utc']) is not str or len(row['captured_utc']) > 64
                    or datetime.fromisoformat(row['captured_utc']).utcoffset() is None):
                raise core.BundleError('invalid_restored_journal_mapping')
            item = indexed.get(row['path'])
            if item is None or item['bytes'] != row['bytes'] or item['sha256'] != row['sha256']:
                raise core.BundleError('restored_journal_mapping_changed')
            seen.add(row['path'])
            if row['path'] == journal_path:
                selected = {scope: receipt.directory / directories[scope] for scope in row['scopes']}
        if selected is None:
            raise core.BundleError('journal_not_in_prefix_capture')
        if any(not path.is_dir() for path in selected.values()):
            raise core.BundleError('restored_object_directory_missing')
        core._budget(deadline, clock)
        return selected
    except core.BundleError:
        raise
    except Exception:
        raise core.BundleError('restored_prefix_mapping_invalid') from None
