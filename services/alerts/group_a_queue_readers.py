"""Acquire identity-checked Group A readers in a dedicated Linux watcher."""

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
import stat
import sys

from services.alerts.group_a_observations import _directory, _observe
from services.alerts.group_a_watch import HostObservation, WatchFinding, WatchReport, _ACCOUNT_RULES, assess_group_a_watch
from services.alerts.group_a_watch_cycle import (
    QueueEventEvidence, QueueReaderUnusable, WatchCycleResult, _epoch_ms, _valid_clock,
    capture_queue_copy, capture_resources,
)
from services.control.group_a_systemd_policy import render_group_a_policy


_FILES = ("intent_queue.sqlite", "intent_queue.sqlite-wal", "intent_queue.sqlite-shm")
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
_FD_CAP = 256


@dataclass(frozen=True)
class QueueIdentity:
    account_data: tuple[int, int]
    database: tuple[int, int]


@dataclass(frozen=True)
class ReleaseIdentity:
    root: tuple[int, int]
    queues: dict[str, QueueIdentity]


def _identity(info):
    return info.st_dev, info.st_ino


def _valid_identity(value):
    return (type(value) is tuple and len(value) == 2
            and all(type(n) is int for n in value) and value[0] >= 0 and value[1] > 0)


def _readonly(fd):
    return bool(os.fstatvfs(fd).f_flag & os.ST_RDONLY)


def _regular_fds(directory):
    result = {}
    with os.scandir(directory) as entries:
        for index, entry in enumerate(entries):
            if index >= _FD_CAP or not entry.name.isascii() or not entry.name.isdecimal():
                raise ValueError("watcher_fd_inventory_invalid")
            fd = int(entry.name)
            try:
                info = os.fstat(fd)
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode):
                result[fd] = _identity(info)
    return result


def _single_linux_thread():
    if sys.platform != "linux":
        return False
    try:
        with os.scandir("/proc/self/task") as entries:
            return next(entries, None) is not None and next(entries, None) is None
    except OSError:
        return False


def _pin_file(parent, name):
    fd = os.open(name, _FILE_FLAGS, dir_fd=parent)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not _readonly(fd):
            raise ValueError("unsafe_queue_file")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _verify_names(parent, identities):
    if not _readonly(parent):
        raise ValueError("queue_mount_not_readonly")
    for name, identity in zip(_FILES, identities, strict=True):
        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or _identity(info) != identity):
            raise ValueError("queue_name_replaced")


def _verify_open_fds(baseline, opened, expected, *, require_wal=False):
    new_fds = {fd: identity for fd, identity in opened.items() if baseline.get(fd) != identity}
    new = list(new_fds.values())
    if (new.count(expected[0]) != 1 or any(identity not in expected for identity in new)
            or any(not _readonly(fd) for fd in new_fds)
            or (require_wal and expected[1] not in new)):
        raise ValueError("sqlite_descriptor_identity_mismatch")


@contextmanager
def _queue_reader(root_fd, account, expected, *, anchor, inventory):
    with ExitStack() as stack:
        data_fd = stack.enter_context(_directory((account, "data"), parent=root_fd))
        if _identity(os.fstat(data_fd)) != expected.account_data or not _readonly(data_fd):
            raise ValueError("queue_directory_identity_mismatch")
        pins = []
        for name in _FILES:
            fd = _pin_file(data_fd, name)
            stack.callback(os.close, fd)
            pins.append(fd)
        identities = tuple(_identity(os.fstat(fd)) for fd in pins)
        if identities[0] != expected.database or len(set(identities)) != len(_FILES):
            raise ValueError("queue_file_identity_mismatch")
        _verify_names(data_fd, identities)
        baseline = inventory()
        if any(identity in identities for fd, identity in baseline.items() if fd not in pins):
            raise ValueError("queue_already_open_in_watcher")

        source = sqlite3.connect(anchor(data_fd).as_uri() + "?mode=ro", uri=True, timeout=0)
        stack.callback(source.close)
        _verify_open_fds(baseline, inventory(), identities)
        source.execute("PRAGMA query_only=ON")
        if source.execute("PRAGMA main.journal_mode").fetchone() != ("wal",):
            raise ValueError("queue_reader_not_wal")
        _verify_names(data_fd, identities)
        yield source, identities
        _verify_open_fds(baseline, inventory(), identities, require_wal=True)
        _verify_names(data_fd, identities)
        if not all(_readonly(fd) for fd in pins):
            raise ValueError("queue_mount_not_readonly")
        with _directory((account, "data"), parent=root_fd) as current:
            if _identity(os.fstat(current)) != expected.account_data or not _readonly(current):
                raise ValueError("queue_directory_replaced")


def _owned_cycle(release, root, receipt, *, since_ms, proc_fd, anchor, inventory, wall_ms=_epoch_ms,
                 track_events=False):
    if type(release) is not str:
        raise ValueError("invalid_group_a_release")
    policy = render_group_a_policy(release)
    if (type(root) is not type(Path()) or root.anchor != "/" or root.name != release
            or ".." in root.parts):
        raise ValueError("invalid_group_a_release_root")
    prefix = policy.target.removesuffix(".target") + "-"
    scopes = tuple(unit.removesuffix("-strategy.service") for unit in policy.services
                   if unit.endswith("-strategy.service"))
    if (type(receipt) is not ReleaseIdentity or not _valid_identity(receipt.root)
            or type(receipt.queues) is not dict or any(type(key) is not str for key in receipt.queues)
            or set(receipt.queues) != set(scopes)
            or any(type(entry) is not QueueIdentity or not _valid_identity(entry.account_data)
                   or not _valid_identity(entry.database) for entry in receipt.queues.values())):
        raise ValueError("invalid_queue_identity_receipt")
    owned = {receipt.root}
    queue_ids = dict(receipt.queues)
    for entry in queue_ids.values():
        if entry.account_data in owned or entry.database in owned or entry.account_data == entry.database:
            raise ValueError("aliased_queue_identity_receipt")
        owned.update((entry.account_data, entry.database))
    started = wall_ms()
    if not _valid_clock(started) or type(since_ms) is not int or not 0 <= since_ms < started:
        raise ValueError("invalid_group_a_cycle_clock")
    unknown = WatchCycleResult(assess_group_a_watch(release, accounts={}, host=HostObservation()), (),
                               QueueEventEvidence(since_ms, started, ()) if track_events else None,
                               tuple((scope, "unavailable", "unknown") for scope in scopes))
    try:
        with _directory(root.parts) as root_fd:
            if _identity(os.fstat(root_fd)) != receipt.root or not _readonly(root_fd):
                return unknown
            with ExitStack() as stack:
                copies = {}
                copied_identities = {}
                unusable = []
                for scope in scopes:
                    account = scope.removeprefix(prefix)
                    sample = None
                    try:
                        with _queue_reader(
                            root_fd, account, queue_ids[scope], anchor=anchor, inventory=inventory,
                        ) as (source, identities):
                            sample = capture_queue_copy(
                                source, scope=scope, since_ms=since_ms, wall_ms=wall_ms,
                                expected_path=root / account / "data" / _FILES[0],
                            )
                    except QueueReaderUnusable:
                        unusable.append(scope)
                        continue
                    except (OSError, ValueError, sqlite3.Error):
                        if sample is not None:
                            sample.close()
                        continue
                    if sample is not None:
                        stack.callback(sample.close)
                        copies[scope] = sample
                        copied_identities[scope] = identities
                resources = capture_resources(root_fd, proc_fd, wall_ms=wall_ms)
                now_ms = wall_ms()
                if not _valid_clock(now_ms) or now_ms < started:
                    raise ValueError("invalid_group_a_cycle_clock")

                def account_still_matches(scope):
                    if scope not in copied_identities:
                        return True
                    try:
                        with _directory((scope.removeprefix(prefix), "data"), parent=root_fd) as current:
                            if _identity(os.fstat(current)) != queue_ids[scope].account_data:
                                return False
                            _verify_names(current, copied_identities[scope])
                    except (OSError, ValueError):
                        return False
                    return True

                events = {} if track_events else None
                coverage = {}
                report = _observe(
                    release, root, now_ms=now_ms, queues=copies, resources=resources,
                    support=True, root_fd=root_fd, account_still_matches=account_still_matches,
                    queue_events=events,
                    queue_health=coverage,
                )
            with _directory(root.parts) as current:
                if _identity(os.fstat(current)) != receipt.root or not _readonly(current):
                    return unknown
            retired = {scope for scope in copied_identities if not account_still_matches(scope)}
            if retired:
                # One final identity verdict governs the report, event history
                # and health together; never acknowledge a discarded source.
                report = WatchReport(
                    tuple(finding for finding in report.alerts if finding.scope not in retired),
                    tuple(sorted(
                        {finding for finding in report.missing if finding.scope not in retired}
                        | {WatchFinding(scope, rule[1]) for scope in retired for rule in _ACCOUNT_RULES},
                        key=lambda finding: (finding.scope, finding.code),
                    )),
                )
            evidence = None if events is None else QueueEventEvidence(since_ms, now_ms, tuple(
                (scope, (*queue_ids[scope].account_data, *queue_ids[scope].database), keys)
                for scope, keys in events.items() if scope not in retired
            ))
            health = tuple((scope, "complete", coverage.get(scope, "unknown"))
                           if scope in copies and scope not in retired
                           else (scope, "unavailable", "unknown") for scope in scopes)
            return WatchCycleResult(report, tuple(unusable), evidence, health)
    except (OSError, sqlite3.Error):
        return unknown


def observe_owned_group_a_queues(release: str, receipt: ReleaseIdentity, *, since_ms: int, proc_fd=None,
                                 track_events=False):
    """One observation in an already verified, single-thread Linux namespace."""
    if type(release) is not str:
        raise ValueError("invalid_group_a_release")
    render_group_a_policy(release)
    if not _single_linux_thread():
        raise ValueError("dedicated_linux_watcher_required")
    return _owned_cycle(
        release, Path("/srv/cryptkeep/state") / release, receipt, since_ms=since_ms, proc_fd=proc_fd,
        anchor=lambda fd: Path(f"/proc/self/fd/{fd}") / _FILES[0],
        inventory=lambda: _regular_fds("/proc/self/fd"),
        track_events=track_events,
    )
