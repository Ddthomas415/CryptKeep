from contextlib import closing
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from services.alerts import group_a_watch_cycle as cycle
from services.alerts.group_a_support_observations import observe_queue
from services.alerts.group_a_watch import WatchFinding


NOW = 1_790_000_000_000
RELEASE = "frozen42"
SCOPE = "cbp-group-a-frozen42-breakout-default-btc"
OTHER_SCOPE = "cbp-group-a-frozen42-breakout-default-eth"
TARGET = "cbp-group-a-frozen42.target"


def _queue_path(root, account="breakout-default-btc"):
    path = root / account / "data" / "intent_queue.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _setup_writer(path, *, wal=True):
    con = sqlite3.connect(path)
    if wal:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA wal_autocheckpoint=0")
    con.executescript("""
        CREATE TABLE trade_intents(intent_id TEXT PRIMARY KEY, source, side, status,
            created_ts, updated_ts, client_order_id, meta, venue, symbol);
        CREATE TABLE paper_exit_events(intent_id, ts, event);
        CREATE TABLE paper_buy_events(intent_id, ts, event, status);
    """)
    return con


def _record(con, *, identity="expired", seconds=10, status="expired"):
    stamp = datetime.fromtimestamp(NOW / 1000 - seconds, timezone.utc).isoformat()
    con.execute("INSERT INTO trade_intents VALUES(?,?,?,?,?,?,?,?,?,?)", (
        identity, "strategy", "buy", status, stamp, stamp, None, None, "coinbase", "BTC/USD",
    ))
    con.commit()


def _reader(path):
    con = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0)
    con.execute("PRAGMA query_only=ON")
    return con


def test_copy_reads_committed_wal_and_preserves_caller_connection(tmp_path):
    path = _queue_path(tmp_path / RELEASE)
    with closing(_setup_writer(path, wal=True)) as writer:
        _record(writer)
        assert Path(str(path) + "-wal").stat().st_size > 0
        with closing(_reader(path)) as reader:
            sample = cycle.capture_queue_copy(
                reader, scope=SCOPE, expected_path=path, since_ms=NOW - 20_000, wall_ms=lambda: NOW,
            )
            assert sample is not None
            with closing(sample):
                _record(writer, identity="later", seconds=2, status="rejected")
                result = observe_queue(sample, market="BTC/USD", now_ms=NOW)
                assert result.order_expired is True and result.order_refused is False
            assert reader.execute("SELECT count(*) FROM trade_intents").fetchone() == (2,)
            assert reader.total_changes == 0 and not reader.in_transaction


def test_wal_commit_during_paged_copy_does_not_change_the_pinned_snapshot(tmp_path):
    path = _queue_path(tmp_path / RELEASE)
    with closing(_setup_writer(path, wal=True)) as writer:
        _record(writer)
        writer.execute("CREATE TABLE padding(data)")
        writer.execute("INSERT INTO padding VALUES(zeroblob(262144))")
        writer.commit()
        calls = 0

        def monotonic():
            nonlocal calls
            calls += 1
            if calls == 2:
                _record(writer, identity="during", seconds=2, status="rejected")
            return 0

        with closing(_reader(path)) as reader:
            sample = cycle.capture_queue_copy(
                reader, scope=SCOPE, expected_path=path, since_ms=NOW - 20_000,
                wall_ms=lambda: NOW, monotonic_ns=monotonic,
            )
            assert sample is not None and calls > 2
            with closing(sample):
                report = observe_queue(sample, market="BTC/USD", now_ms=NOW)
                assert report.order_expired is True and report.order_refused is False
            assert reader.execute("SELECT count(*) FROM trade_intents").fetchone() == (2,)


def test_copy_refuses_wrong_source_busy_budget_and_caller_transaction(tmp_path, monkeypatch):
    path = _queue_path(tmp_path / RELEASE)
    with closing(_setup_writer(path)) as writer:
        _record(writer)
    with closing(_reader(path)) as reader:
        options = {"scope": SCOPE, "expected_path": path, "since_ms": NOW - 20_000, "wall_ms": lambda: NOW}
        assert cycle.capture_queue_copy(reader, **{**options, "expected_path": path.with_name("other")}) is None
        reader.execute("PRAGMA busy_timeout=20")
        assert cycle.capture_queue_copy(reader, **options) is None
        reader.execute("PRAGMA busy_timeout=0")
        reader.execute("BEGIN")
        assert cycle.capture_queue_copy(reader, **options) is None
        assert reader.in_transaction
        reader.execute("ROLLBACK")
        steps = iter((0, cycle._COPY_NS + 1))
        assert cycle.capture_queue_copy(reader, **options, monotonic_ns=lambda: next(steps)) is None
        assert not reader.in_transaction
        monkeypatch.setattr(cycle, "_MAX_QUEUE_BYTES", 1024)
        assert cycle.capture_queue_copy(reader, **options) is None
        assert not reader.in_transaction


def test_copy_does_not_accept_unnamed_database(tmp_path):
    with closing(sqlite3.connect("", timeout=0)) as source:
        source.execute("PRAGMA query_only=ON")
        assert cycle.capture_queue_copy(
            source, scope=SCOPE, expected_path=tmp_path / "intent_queue.sqlite",
            since_ms=NOW - 20_000, wall_ms=lambda: NOW,
        ) is None


def test_immutable_reader_cannot_omit_committed_wal_rows(tmp_path):
    path = _queue_path(tmp_path / RELEASE)
    with closing(_setup_writer(path, wal=True)):
        pass  # Put the schema in the main file first.
    with closing(sqlite3.connect(path)) as writer:
        writer.execute("PRAGMA wal_autocheckpoint=0")
        _record(writer)
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=0)) as reader:
            reader.execute("PRAGMA query_only=ON")
            assert reader.execute("SELECT count(*) FROM trade_intents").fetchone() == (0,)
            sample = cycle.capture_queue_copy(
                reader, scope=SCOPE, expected_path=path, since_ms=NOW - 20_000, wall_ms=lambda: NOW,
            )
            if sample is not None:
                sample.close()
            assert sample is None


def test_denied_rollback_isolated_and_caller_reader_flagged(tmp_path):
    root = tmp_path.resolve() / RELEASE
    bad_path = _queue_path(root)
    good_path = _queue_path(root, "breakout-default-eth")
    with closing(_setup_writer(bad_path, wal=True)) as writer:
        _record(writer)
    with closing(_setup_writer(good_path, wal=True)) as writer:
        stamp = datetime.fromtimestamp(NOW / 1000 - 10, timezone.utc).isoformat()
        writer.execute("INSERT INTO trade_intents VALUES(?,?,?,?,?,?,?,?,?,?)", (
            "eth", "strategy", "buy", "expired", stamp, stamp, None, None, "coinbase", "ETH/USD",
        ))
        writer.commit()
    with closing(_reader(bad_path)) as bad, closing(_reader(good_path)) as good:
        bad.set_authorizer(lambda action, arg, *_: (
            sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_TRANSACTION and arg == "ROLLBACK" else sqlite3.SQLITE_OK
        ))
        result = cycle.observe_group_a_cycle(
            RELEASE, root, sources={SCOPE: bad, OTHER_SCOPE: good}, since_ms=NOW - 20_000, wall_ms=lambda: NOW,
        )
        assert result.unusable_readers == (SCOPE,)
        assert WatchFinding(SCOPE, "order_expired") in result.report.missing
        assert WatchFinding(OTHER_SCOPE, "order_expired") in result.report.alerts
        assert bad.in_transaction and not good.in_transaction
        bad.set_authorizer(None)
        bad.execute("ROLLBACK")


def test_cycle_classifies_trusted_synthetic_sources_and_leaves_cutoff_with_caller(tmp_path, monkeypatch):
    root = tmp_path.resolve() / RELEASE
    path = _queue_path(root)
    proc = tmp_path / "proc"
    proc.mkdir()
    (proc / "meminfo").write_bytes(b"MemTotal: 1000 kB\nMemAvailable: 140 kB\n")
    proc_fd = os.open(proc, os.O_RDONLY | os.O_DIRECTORY)
    monkeypatch.setattr(cycle.os, "fstatvfs", lambda _: SimpleNamespace(f_blocks=100, f_bfree=15, f_bavail=10))
    try:
        with closing(_setup_writer(path)) as writer:
            _record(writer)
        with closing(_reader(path)) as reader:
            options = dict(sources={SCOPE: reader}, proc_fd=proc_fd, wall_ms=lambda: NOW)
            outcome = cycle.observe_group_a_cycle(RELEASE, root, since_ms=NOW - 20_000, **options)
            assert outcome.unusable_readers == ()
            first = outcome.report
            second = cycle.observe_group_a_cycle(RELEASE, root, since_ms=NOW - 20_000, **options).report
            later = cycle.observe_group_a_cycle(RELEASE, root, since_ms=NOW - 10_000, **options).report
            assert first == second
            assert WatchFinding(SCOPE, "order_expired") in first.alerts
            assert WatchFinding(SCOPE, "order_expired") not in later.alerts
            assert WatchFinding(OTHER_SCOPE, "order_expired") in first.missing
            assert WatchFinding(TARGET, "disk_high") in first.alerts
            assert WatchFinding(TARGET, "memory_high") in first.alerts
            assert WatchFinding(TARGET, "backup_failed") in first.missing
            with pytest.raises(ValueError, match="queue_sources"):
                cycle.observe_group_a_cycle(RELEASE, root, sources={SCOPE: reader, OTHER_SCOPE: reader},
                                            since_ms=NOW - 20_000, wall_ms=lambda: NOW)
    finally:
        os.close(proc_fd)


def test_missing_root_and_linked_meminfo_do_not_invent_observations(tmp_path):
    missing = tmp_path.resolve() / RELEASE
    report = cycle.observe_group_a_cycle(
        RELEASE, missing, sources={}, since_ms=NOW - 10_000, wall_ms=lambda: NOW,
    ).report
    assert not missing.exists() and not report.alerts and len(report.missing) == 93
    data = tmp_path / "actual"
    data.write_text("MemTotal: 1000 kB\nMemAvailable: 1 kB\n")
    (tmp_path / "meminfo").symlink_to(data)
    directory = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert cycle.capture_resources(directory, directory, wall_ms=lambda: NOW).meminfo == b""
    finally:
        os.close(directory)
