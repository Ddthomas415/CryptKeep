from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import select
import sqlite3
import subprocess
import sys

import pytest

from services.alerts import group_a_observations as observations
from services.alerts import group_a_queue_readers as readers
from services.alerts.group_a_delivery import deliver_group_a_cycle
from services.alerts.group_a_watch import WatchFinding
from services.alerts.group_a_watch_cycle import capture_queue_copy
from services.control.group_a_systemd_policy import render_group_a_policy


RELEASE = "frozen42"
PREFIX = "cbp-group-a-frozen42-"
ACCOUNT = "breakout-default-btc"
SCOPE = PREFIX + ACCOUNT
NOW = 1_790_000_000_000
DATABASE = "intent_queue.sqlite"


@contextmanager
def _keeper(path):
    # A separate synthetic writer keeps both sidecars open while the reader runs.
    code = """
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.execute("PRAGMA journal_mode=WAL")
c.execute("PRAGMA wal_autocheckpoint=0")
c.executescript('''
    CREATE TABLE trade_intents(intent_id TEXT PRIMARY KEY, source, side, status,
        created_ts, updated_ts, client_order_id, meta, venue, symbol);
    CREATE TABLE paper_exit_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT, intent_id, ts, event);
    CREATE TABLE paper_buy_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT, intent_id, ts, event, status);
    INSERT INTO trade_intents VALUES ('test','strategy','buy','expired',
        '2026-09-21T14:13:10+00:00','2026-09-21T14:13:10+00:00',
        NULL,NULL,'coinbase','BTC/USD');
''')
print("ready", flush=True)
sys.stdin.read()
c.close()
"""
    child = subprocess.Popen(
        [sys.executable, "-B", "-c", code, str(path)], env={"PATH": "/usr/bin:/bin"},
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        assert select.select([child.stdout], [], [], 5)[0] and child.stdout.readline() == "ready\n"
        yield
    finally:
        child.communicate(timeout=5)
        assert child.returncode == 0


def _setup(tmp_path):
    root = tmp_path.resolve() / RELEASE
    paths = {}
    for unit in render_group_a_policy(RELEASE).services:
        if unit.endswith("-strategy.service"):
            scope = unit.removesuffix("-strategy.service")
            path = root / scope.removeprefix(PREFIX) / "data" / DATABASE
            path.parent.mkdir(parents=True)
            path.touch()
            paths[scope] = path
    return root, paths


def _receipt(root, paths):
    return readers.ReleaseIdentity(readers._identity(root.stat()), {
        scope: readers.QueueIdentity(readers._identity(path.parent.stat()), readers._identity(path.stat()))
        for scope, path in paths.items()
    })


def _inventory():
    return readers._regular_fds("/proc/self/fd" if sys.platform == "linux" else "/dev/fd")


def test_real_sqlite_descriptor_and_wal_copy_with_synthetic_mount_check(tmp_path, monkeypatch):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)
    with _keeper(db):
        receipt = _receipt(root, paths)
        result = readers._owned_cycle(
            RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
            anchor=lambda fd: db, inventory=_inventory, wall_ms=lambda: NOW,
        )
        assert WatchFinding(SCOPE, "order_expired") in result.report.alerts
        assert result.unusable_readers == ()
        assert (SCOPE, "complete", "complete") in result.queue_health
        assert all(row[1:] == ("unavailable", "unknown") for row in result.queue_health if row[0] != SCOPE)


def test_retained_wal_events_rearm_delivery_for_late_same_timestamp_commit(tmp_path, monkeypatch):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    cursor = tmp_path.resolve() / "group_a_delivery.sqlite"
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)
    with _keeper(db):
        receipt = _receipt(root, paths)

        def poll(now):
            observation = readers._owned_cycle(
                RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
                anchor=lambda fd: db, inventory=_inventory, wall_ms=lambda: now, track_events=True,
            )
            evidence = observation.queue_events
            assert [batch[0] for batch in evidence.accounts] == [SCOPE]
            attempt = deliver_group_a_cycle(
                cursor, RELEASE, observation.report, observed_ms=now, queue_events=evidence, cfg={},
                send_alert=lambda **_: {"ok": True, "channels": [{"channel": "slack", "ok": True, "status": 200}]},
            )
            return len(evidence.accounts[0][2]), attempt.outcome

        assert poll(NOW) == (1, "slack_accepted")
        writer = sqlite3.connect(db)
        try:
            with writer:
                writer.execute("INSERT INTO trade_intents SELECT 'second', source, side, status, "
                               "created_ts, updated_ts, client_order_id, meta, venue, symbol FROM trade_intents")
                writer.execute("INSERT INTO paper_buy_events(intent_id, ts, event, status) "
                               "SELECT intent_id, updated_ts, 'transition', status FROM trade_intents")
        finally:
            writer.close()
        # Each delivery call reopens the durable cursor. The history rows do
        # not duplicate the current terminal state, and timestamps do not gate replay.
        assert poll(NOW + 1) == (2, "slack_accepted")
        assert poll(NOW + 2) == (2, "idle")
        writer = sqlite3.connect(db)
        try:
            with writer:
                writer.execute("INSERT INTO trade_intents SELECT 'sell', source, 'sell', 'filled', "
                               "created_ts, updated_ts, client_order_id, meta, venue, symbol "
                               "FROM trade_intents WHERE intent_id='test'")
                for _ in range(2):
                    writer.execute("INSERT INTO paper_exit_events(intent_id, ts, event) "
                                   "SELECT intent_id, updated_ts, 'refused' FROM trade_intents WHERE intent_id='sell'")
        finally:
            writer.close()
        # Repeated exit refusals are separate evidence rows, coalesced into one notice.
        assert poll(NOW + 3) == (4, "slack_accepted")
        assert poll(NOW + 4) == (4, "idle")


def test_tracked_delivery_rejects_report_time_before_actual_observation(tmp_path, monkeypatch):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    cursor = tmp_path.resolve() / "group_a_delivery.sqlite"
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)
    with _keeper(db):
        result = readers._owned_cycle(
            RELEASE, root, _receipt(root, paths), since_ms=NOW - 20_000, proc_fd=None,
            anchor=lambda _: db, inventory=_inventory, wall_ms=lambda: NOW, track_events=True,
        )
        with pytest.raises(ValueError, match="invalid_group_a_queue_evidence"):
            deliver_group_a_cycle(
                cursor, RELEASE, result.report, observed_ms=NOW - 15_000, queue_events=result.queue_events, cfg={},
                send_alert=lambda **_: pytest.fail("sent before the captured observation"),
            )
        assert not cursor.exists()


def test_old_journal_expiry_does_not_cross_cutoff_after_metadata_update(tmp_path, monkeypatch):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)
    with _keeper(db):
        writer = sqlite3.connect(db)
        try:
            with writer:
                writer.execute("INSERT INTO paper_buy_events(intent_id, ts, event, status) "
                               "SELECT intent_id, updated_ts, 'transition', status FROM trade_intents")
                updated = datetime.fromtimestamp((NOW - 1000) / 1000, tz=timezone.utc).isoformat()
                writer.execute("UPDATE trade_intents SET client_order_id='metadata-only', updated_ts=?", (updated,))
        finally:
            writer.close()
        result = readers._owned_cycle(
            RELEASE, root, _receipt(root, paths), since_ms=NOW - 5_000, proc_fd=None,
            anchor=lambda _: db, inventory=_inventory, wall_ms=lambda: NOW, track_events=True,
        )
        finding = WatchFinding(SCOPE, "order_expired")
        assert finding not in result.report.alerts and finding not in result.report.missing
        assert len(result.queue_events.accounts) == 1 and result.queue_events.accounts[0][2] == ()


def test_writable_mount_and_missing_sidecars_do_not_open_sqlite(tmp_path, monkeypatch):
    root, paths = _setup(tmp_path)
    receipt = _receipt(root, paths)
    with monkeypatch.context() as context:
        context.setattr(readers, "_readonly", lambda fd: False)
        context.setattr(readers.sqlite3, "connect", lambda *_a, **_kw: pytest.fail("opened database"))
        out = readers._owned_cycle(
            RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
            anchor=lambda fd: paths[SCOPE], inventory=_inventory, wall_ms=lambda: NOW,
        )
        assert not out.report.alerts and len(out.report.missing) == 93
        context.setattr(readers, "_readonly", lambda fd: True)
        out = readers._owned_cycle(
            RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
            anchor=lambda fd: paths[SCOPE], inventory=_inventory, wall_ms=lambda: NOW,
        )
        assert WatchFinding(SCOPE, "order_expired") in out.report.missing


def test_wrong_sqlite_inode_and_aliased_receipt_rejected(tmp_path, monkeypatch):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    other = tmp_path / "other.sqlite"
    with sqlite3.connect(other) as con:
        con.execute("CREATE TABLE marker(x)")
    con.close()
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)
    with _keeper(db):
        receipt = _receipt(root, paths)
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            with pytest.raises(ValueError, match="descriptor_identity"):
                with readers._queue_reader(fd, ACCOUNT, receipt.queues[SCOPE], anchor=lambda _: other,
                                           inventory=_inventory):
                    pytest.fail("exposed wrong reader")
        finally:
            os.close(fd)
        other_scope = next(scope for scope in paths if scope != SCOPE)
        receipt.queues[other_scope] = receipt.queues[SCOPE]
        with pytest.raises(ValueError, match="aliased_queue"):
            readers._owned_cycle(
                RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
                anchor=lambda fd: db, inventory=_inventory, wall_ms=lambda: NOW,
            )


def test_changed_main_name_discards_a_completed_copy(tmp_path, monkeypatch):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    moved = db.with_name("old.sqlite")
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)

    def replace_after_copy(*args, **kwargs):
        sample = capture_queue_copy(*args, **kwargs)
        assert sample is not None
        db.rename(moved)
        db.touch()
        return sample

    monkeypatch.setattr(readers, "capture_queue_copy", replace_after_copy)
    with _keeper(db):
        receipt = _receipt(root, paths)
        try:
            result = readers._owned_cycle(
                RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
                anchor=lambda fd: db, inventory=_inventory, wall_ms=lambda: NOW,
            )
            assert WatchFinding(SCOPE, "order_expired") in result.report.missing
            assert WatchFinding(SCOPE, "order_expired") not in result.report.alerts
        finally:
            moved.replace(db)


@pytest.mark.parametrize("replace_account", [True, False], ids=["account", "queue"])
def test_replacement_during_composition_discards_only_affected_account(tmp_path, monkeypatch, replace_account):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    other_scope = next(scope for scope in paths if scope != SCOPE)
    other_db = paths[other_scope]
    original = observations._account
    renamed = db.parent.parent if replace_account else db
    moved = renamed.with_name(renamed.name + ".old")
    stale = datetime.fromtimestamp(NOW / 1000 - 900, tz=timezone.utc).isoformat()

    def write_status(path):
        flags = path.parent.parent / "runtime" / "flags"
        flags.mkdir(parents=True, exist_ok=True)
        (flags / "strategy_runner.status.json").write_text(json.dumps({"ok": True, "ts": stale}))

    def replace_while_reading(root_fd, account, market, now_ms):
        if account == ACCOUNT:
            renamed.rename(moved)
            db.parent.mkdir(parents=True, exist_ok=True)
            db.touch()
            write_status(db)
        return original(root_fd, account, market, now_ms)

    write_status(other_db)
    monkeypatch.setattr(observations, "_account", replace_while_reading)
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)
    with _keeper(db):
        receipt = _receipt(root, paths)
        try:
            out = readers._owned_cycle(
                RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
                anchor=lambda fd: db, inventory=_inventory, wall_ms=lambda: NOW,
            )
            assert WatchFinding(SCOPE, "order_expired") in out.report.missing
            assert not any(finding.scope == SCOPE for finding in out.report.alerts)
            assert any(finding.scope == other_scope for finding in out.report.alerts)
        finally:
            if replace_account:
                renamed.rename(renamed.with_name(renamed.name + ".replacement"))
            moved.replace(renamed)


def test_replaced_release_directory_discards_whole_cycle(tmp_path, monkeypatch):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    moved = root.with_name("moved")
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)

    def replace_root_after_copy(*args, **kwargs):
        sample = capture_queue_copy(*args, **kwargs)
        assert sample is not None
        root.rename(moved)
        root.mkdir()
        return sample

    monkeypatch.setattr(readers, "capture_queue_copy", replace_root_after_copy)
    with _keeper(db):
        receipt = _receipt(root, paths)
        try:
            result = readers._owned_cycle(
                RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
                anchor=lambda fd: db, inventory=_inventory, wall_ms=lambda: NOW,
            )
            assert not result.report.alerts and len(result.report.missing) == 93
        finally:
            root.rmdir()
            moved.rename(root)


@pytest.mark.parametrize("replace_account", [True, False], ids=["account", "queue"])
def test_final_identity_failure_discards_report_and_events_together(tmp_path, monkeypatch, replace_account):
    root, paths = _setup(tmp_path)
    db = paths[SCOPE]
    other_scope = next(scope for scope in paths if scope != SCOPE)
    flags = paths[other_scope].parent.parent / "runtime" / "flags"
    flags.mkdir(parents=True)
    stale = datetime.fromtimestamp(NOW / 1000 - 900, tz=timezone.utc).isoformat()
    (flags / "strategy_runner.status.json").write_text(json.dumps({"ok": True, "ts": stale}))
    original = readers._observe
    renamed = db.parent.parent if replace_account else db
    moved = renamed.with_name(renamed.name + ".retired")
    def replace_after_composition(*args, **kwargs):
        report = original(*args, **kwargs)
        assert WatchFinding(SCOPE, "order_expired") in report.alerts
        renamed.rename(moved)
        db.parent.mkdir(parents=True, exist_ok=True)
        db.touch()
        return report
    monkeypatch.setattr(readers, "_observe", replace_after_composition)
    monkeypatch.setattr(readers, "_readonly", lambda fd: True)
    with _keeper(db):
        receipt = _receipt(root, paths)
        try:
            result = readers._owned_cycle(RELEASE, root, receipt, since_ms=NOW - 20_000, proc_fd=None,
                                          anchor=lambda fd: db, inventory=_inventory, wall_ms=lambda: NOW,
                                          track_events=True)
            assert not any(f.scope == SCOPE for f in result.report.alerts)
            assert WatchFinding(SCOPE, "order_expired") in result.report.missing
            assert not any(row[0] == SCOPE for row in result.queue_events.accounts)
            assert (SCOPE, "unavailable", "unknown") in result.queue_health
            assert WatchFinding(other_scope, "strategy_status_stale") in result.report.alerts
        finally:
            if replace_account:
                renamed.rename(renamed.with_name(renamed.name + ".replacement"))
            moved.replace(renamed)
