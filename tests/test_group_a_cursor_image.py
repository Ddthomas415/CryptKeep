from contextlib import contextmanager
from hashlib import sha256
import os
import sqlite3
import subprocess
import sys

import pytest

from services.alerts import group_a_cursor_image as image
from services.alerts.group_a_delivery import DeliveryUnconfirmed, deliver_group_a_image_cycle
from services.alerts.group_a_watch import HostObservation, assess_group_a_watch
from services.alerts.group_a_watch_cycle import QueueEventEvidence


ACCEPTED = {"ok": True, "channels": [{"channel": "slack", "ok": True, "status": 200}]}


@contextmanager
def _directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        yield fd
    finally:
        os.close(fd)


@pytest.fixture
def cursor(tmp_path):
    path = tmp_path / "cursor"
    path.mkdir(mode=0o700)
    seed = path / image.IMAGE_NAME
    seed.write_bytes(image.EMPTY_IMAGE)
    seed.chmod(0o600)
    return path


def _run(fd, stamp, send=lambda **_: ACCEPTED):
    report = assess_group_a_watch("frozen42", accounts={}, host=HostObservation(disk_pct=81))
    return deliver_group_a_image_cycle(fd, "frozen42", report, observed_ms=stamp,
                                      queue_events=QueueEventEvidence(0, stamp, ()), cfg={}, send_alert=send)


def _no_send(**_):
    pytest.fail("unexpected external attempt")


def test_serialized_cursor_reopens_and_ignores_legacy_sqlite_names(cursor):
    outside = cursor.parent / "outside"
    outside.write_bytes(b"unchanged")
    for name in ("group_a_delivery.sqlite", "group_a_delivery.sqlite-journal"):
        (cursor / name).symlink_to(outside)
    with _directory(cursor) as fd:
        assert _run(fd, 1).outcome == "slack_accepted"
        assert _run(fd, 2, send=_no_send).outcome == "idle"
    assert outside.read_bytes() == b"unchanged"
    assert {path.name for path in cursor.iterdir()} == {
        image.IMAGE_NAME, "group_a_delivery.sqlite", "group_a_delivery.sqlite-journal",
    }


def test_symlink_inserted_at_replace_never_redirects_write(cursor, monkeypatch):
    outside = cursor.parent / "outside"
    outside.write_bytes(b"unchanged")
    target = cursor / image.IMAGE_NAME
    replace = os.replace

    def race(src, dst, *, src_dir_fd, dst_dir_fd):
        assert dst == image.IMAGE_NAME and src_dir_fd == dst_dir_fd
        target.unlink()
        target.symlink_to(outside)
        return replace(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    monkeypatch.setattr(image.os, "replace", race)
    with _directory(cursor) as fd:
        assert _run(fd, 1).outcome == "slack_accepted"
        assert _run(fd, 2, send=_no_send).outcome == "idle"
    assert outside.read_bytes() == b"unchanged" and not target.is_symlink()


@pytest.mark.parametrize("damage", ["missing", "symlink", "hardlink", "corrupt"])
def test_bad_or_lost_seed_does_not_reinitialize(cursor, damage):
    target = cursor / image.IMAGE_NAME
    outside = cursor.parent / "outside"
    outside.write_bytes(image.EMPTY_IMAGE)
    outside.chmod(0o600)
    target.unlink()
    if damage == "symlink":
        target.symlink_to(outside)
    elif damage == "hardlink":
        os.link(outside, target)
    elif damage == "corrupt":
        target.write_bytes(image.EMPTY_IMAGE + b"bad" * 30)
        target.chmod(0o600)
    with _directory(cursor) as fd, pytest.raises((OSError, ValueError)):
        _run(fd, 1, send=_no_send)
    assert outside.read_bytes() == image.EMPTY_IMAGE


def test_same_directory_descriptor_cannot_reenter_during_send(cursor):
    with _directory(cursor) as fd:
        def contender(**_):
            with pytest.raises(BlockingIOError):
                _run(fd, 2, send=_no_send)
            return ACCEPTED

        assert _run(fd, 1, send=contender).outcome == "slack_accepted"
        assert _run(fd, 2, send=_no_send).outcome == "idle"


@pytest.mark.parametrize("fail_at", [2, 3, 4])
def test_storage_failure_is_not_reported_as_delivery_success(cursor, monkeypatch, fail_at):
    fsync = os.fsync
    calls, sent = [], []

    def fail_once(fd):
        calls.append(fd)
        if len(calls) == fail_at:
            raise OSError("synthetic persistence failure")
        return fsync(fd)

    def send(**_):
        sent.append(True)
        return ACCEPTED

    monkeypatch.setattr(image.os, "fsync", fail_once)
    with _directory(cursor) as fd:
        with pytest.raises(OSError if fail_at == 2 else DeliveryUnconfirmed):
            _run(fd, 1, send=send)
        assert len(sent) == int(fail_at > 2)
        expected = "idle" if fail_at == 4 else "slack_accepted"
        assert _run(fd, 2, send=send).outcome == expected


def test_hard_process_exit_preserves_pending_image(cursor):
    child = '''
import os, sys
from services.alerts.group_a_delivery import deliver_group_a_image_cycle
from services.alerts.group_a_watch import HostObservation, assess_group_a_watch
from services.alerts.group_a_watch_cycle import QueueEventEvidence
report = assess_group_a_watch("frozen42", accounts={}, host=HostObservation(disk_pct=81))
deliver_group_a_image_cycle(int(sys.argv[1]), "frozen42", report, observed_ms=1, cfg={},
                            send_alert=lambda **_: os._exit(23), queue_events=QueueEventEvidence(0, 1, ()))
'''
    with _directory(cursor) as fd:
        result = subprocess.run([sys.executable, "-B", "-c", child, str(fd)], pass_fds=(fd,),
                                check=False, timeout=5, env={"PATH": "/usr/bin:/bin"})
        assert result.returncode == 23
        assert _run(fd, 2).outcome == "slack_accepted"


@pytest.mark.parametrize("damage", ["missing_tables", "reserved_trigger", "wrong_columns"])
def test_checksum_valid_but_unsupported_schema_is_rejected(cursor, damage):
    target = cursor / image.IMAGE_NAME
    with _directory(cursor) as fd:
        assert _run(fd, 1).outcome == "slack_accepted"
    raw = target.read_bytes()
    connection = sqlite3.connect(":memory:")
    try:
        if damage == "missing_tables":
            connection.execute("CREATE TABLE temporary_marker(x)")
            connection.execute("DROP TABLE temporary_marker")
        else:
            connection.deserialize(raw[image._HEADER:])
            if damage == "reserved_trigger":
                connection.execute("PRAGMA writable_schema=ON")
                connection.execute("""CREATE TRIGGER sqlite_suppress_alert AFTER INSERT ON delivery_finding
                    BEGIN UPDATE delivery_finding SET pending=0; END""")
            else:
                connection.execute("ALTER TABLE delivery_cycle ADD COLUMN unexpected TEXT")
        connection.commit()
        changed = connection.serialize()
    finally:
        connection.close()
    replacement = image.EMPTY_IMAGE + sha256(changed).digest() + changed
    target.write_bytes(replacement)
    with _directory(cursor) as fd, pytest.raises(ValueError, match="unsafe_alert_cursor_schema"):
        _run(fd, 2, send=_no_send)
    assert target.read_bytes() == replacement
