"""One bounded Group A observation cycle; no connection opening on disk or sending."""

from contextlib import ExitStack
from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
import stat
import time

from services.alerts.group_a_observations import _directory, _observe
from services.alerts.group_a_support_observations import QueueSample, ResourceSample
from services.alerts.group_a_watch import HostObservation, WatchReport, assess_group_a_watch
from services.control.group_a_systemd_policy import render_group_a_policy


_MAX_QUEUE_BYTES = 4 * 1024 * 1024
_COPY_STEPS = 512
_COPY_NS = 2_000_000_000
_MAX_MEMINFO = 16_384
_MAX_EPOCH_MS = 253_402_300_799_999


class QueueReaderUnusable(RuntimeError):
    """The caller must discard or explicitly recover this borrowed reader."""


@dataclass(frozen=True)
class QueueEventEvidence:
    since_ms: int
    observed_ms: int
    accounts: tuple[tuple[str, tuple[int, int, int, int], tuple[tuple[str, str], ...]], ...]


@dataclass(frozen=True)
class WatchCycleResult:
    report: WatchReport
    unusable_readers: tuple[str, ...]
    queue_events: QueueEventEvidence | None = None
    queue_health: tuple[tuple[str, str, str], ...] = ()


def _epoch_ms():
    return time.time_ns() // 1_000_000


def _valid_clock(value):
    return type(value) is int and 1 <= value <= _MAX_EPOCH_MS


def _source_location(source, expected_path):
    if (type(source) is not sqlite3.Connection or source.row_factory is not None
            or source.text_factory is not str or source.in_transaction):
        return False
    databases = source.execute("PRAGMA database_list").fetchall()
    return (len(databases) == 1 and databases[0][:2] == (0, "main")
            and databases[0][2] == str(expected_path)
            and source.execute("PRAGMA query_only").fetchone() == (1,)
            and source.execute("PRAGMA busy_timeout").fetchone() == (0,))


def capture_queue_copy(source, *, scope, expected_path, since_ms, wall_ms=_epoch_ms, monotonic_ns=time.monotonic_ns):
    """Copy a dedicated caller-owned query-only reader, or return unknown.

    The caller is responsible for safe acquisition and physical identity of the
    reader, and for the completeness of its retained queue/event history.
    """
    if (type(scope) is not str or type(expected_path) is not type(Path())
            or not expected_path.is_absolute() or ".." in expected_path.parts):
        return None
    sample = None
    started_txn = False
    success = False
    try:
        if not _source_location(source, expected_path):
            return None
        captured = wall_ms()
        if not _valid_clock(captured) or type(since_ms) is not int or not 0 <= since_ms < captured:
            return None
        deadline = monotonic_ns() + _COPY_NS
        source.execute("BEGIN")
        started_txn = True
        # Group A's queue uses WAL; immutable readers can ignore its committed frames.
        if source.execute("PRAGMA main.journal_mode").fetchone() != ("wal",):
            return None
        page_size, = source.execute("PRAGMA main.page_size").fetchone()
        pages, = source.execute("PRAGMA main.page_count").fetchone()
        if not 512 <= page_size <= 65_536 or not 0 < pages <= _MAX_QUEUE_BYTES // page_size:
            return None
        sample = QueueSample(scope, captured, since_ms)
        target = sample.connection
        target.execute(f"PRAGMA page_size={page_size}")
        steps = 0

        def progress(status, remaining, total):
            nonlocal steps
            steps += 1
            if (status not in (sqlite3.SQLITE_OK, sqlite3.SQLITE_DONE)
                    or not 0 <= remaining <= total <= _MAX_QUEUE_BYTES // page_size
                    or steps > _COPY_STEPS or monotonic_ns() > deadline):
                raise ValueError("queue_copy_budget_or_busy")

        source.backup(target, pages=32, progress=progress, sleep=0)
        finished = wall_ms()
        if not _valid_clock(finished) or finished < captured:
            return None
        target.execute("PRAGMA trusted_schema=OFF")
        target.execute("PRAGMA temp_store=MEMORY")
        target.execute("PRAGMA query_only=ON")
        success = True
        return sample
    except (sqlite3.Error, OSError, ValueError, TypeError, OverflowError):
        return None
    finally:
        try:
            if started_txn and source.in_transaction:
                source.execute("ROLLBACK")
        except sqlite3.Error:
            success = False
            raise QueueReaderUnusable("queue_reader_cleanup_failed") from None
        finally:
            if sample is not None and not success:
                sample.close()


def capture_resources(root_fd, proc_fd, *, wall_ms=_epoch_ms):
    """Read the release filesystem and fixed meminfo entry from supplied fds."""
    if type(root_fd) is not int or root_fd < 0:
        return None
    captured = wall_ms()
    if not _valid_clock(captured):
        return None
    blocks = free = available = -1
    meminfo = b""
    try:
        fs = os.fstatvfs(root_fd)
        blocks, free, available = fs.f_blocks, fs.f_bfree, fs.f_bavail
    except OSError:
        pass
    if type(proc_fd) is int and proc_fd >= 0:
        try:
            fd = os.open("meminfo", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=proc_fd)
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                if stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                    meminfo = stream.read(_MAX_MEMINFO + 1)
        except OSError:
            pass
    return ResourceSample(captured, blocks, free, available, meminfo)


def observe_group_a_cycle(
    release: str, release_root: Path, *, sources: dict[str, sqlite3.Connection], since_ms: int,
    proc_fd=None, wall_ms=_epoch_ms, monotonic_ns=time.monotonic_ns,
):
    """Capture and classify once; sources stay caller-owned and cutoff is unchanged."""
    if type(release) is not str:
        raise ValueError("invalid_group_a_release")
    policy = render_group_a_policy(release)
    if (type(release_root) is not type(Path()) or not release_root.is_absolute()
            or release_root.anchor != "/" or release_root.name != release or ".." in release_root.parts):
        raise ValueError("invalid_group_a_release_root")
    prefix = policy.target.removesuffix(".target") + "-"
    scopes = tuple(unit.removesuffix("-strategy.service") for unit in policy.services
                   if unit.endswith("-strategy.service"))
    if (type(sources) is not dict or any(type(scope) is not str or scope not in scopes for scope in sources)
            or len({id(source) for source in sources.values()}) != len(sources)):
        raise ValueError("invalid_group_a_queue_sources")
    started = wall_ms()
    if not _valid_clock(started) or type(since_ms) is not int or not 0 <= since_ms < started:
        raise ValueError("invalid_group_a_cycle_clock")
    copies = {}
    unusable_readers = []
    resources = None
    with ExitStack() as stack:
        try:
            root_fd = stack.enter_context(_directory(release_root.parts))
        except OSError:
            root_fd = None
        if root_fd is not None:
            for scope in scopes:
                if scope not in sources:
                    continue
                account = scope.removeprefix(prefix)
                try:
                    sample = capture_queue_copy(
                        sources[scope], scope=scope, since_ms=since_ms,
                        expected_path=release_root / account / "data" / "intent_queue.sqlite",
                        wall_ms=wall_ms, monotonic_ns=monotonic_ns,
                    )
                except QueueReaderUnusable:
                    unusable_readers.append(scope)
                    continue
                if sample is not None:
                    stack.callback(sample.close)
                    copies[scope] = sample
            resources = capture_resources(root_fd, proc_fd, wall_ms=wall_ms)
        now_ms = wall_ms()
        if not _valid_clock(now_ms) or now_ms < started:
            raise ValueError("invalid_group_a_cycle_clock")
        if root_fd is None:
            return WatchCycleResult(assess_group_a_watch(release, accounts={}, host=HostObservation()), ())
        report = _observe(
            release, release_root, now_ms=now_ms, queues=copies, resources=resources,
            support=True, root_fd=root_fd,
        )
        return WatchCycleResult(report, tuple(unusable_readers))
