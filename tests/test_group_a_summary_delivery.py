import json
import os
import sqlite3

import pytest

from services.alerts import group_a_cursor_image as image, group_a_delivery as legacy
from services.alerts.group_a_summary_delivery import deliver_summary
from services.alerts.group_a_summary_protocol import Health, bit_for, control, summary_body
from services.alerts.group_a_watch import (
    AccountObservation, HostObservation, WatchFinding, WatchReport, _account_names, _policy, assess_group_a_watch,
)
from services.alerts.group_a_watch_cycle import QueueEventEvidence, WatchCycleResult


RELEASE = "frozen42"
SCOPE = _account_names(_policy(RELEASE))[0]
REQUEST = control(RELEASE, "a" * 32, 0)


@pytest.fixture
def cursor(tmp_path):
    root = tmp_path / "cursor"
    root.mkdir(mode=0o700)
    target = root / image.IMAGE_NAME
    target.write_bytes(image.EMPTY_IMAGE)
    target.chmod(0o600)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        yield fd, root
    finally:
        os.close(fd)


def observation(stamp, digests=(), *, disk=81):
    report = assess_group_a_watch(RELEASE, accounts={SCOPE: AccountObservation(
        order_refused=False, order_expired=bool(digests),
    )}, host=HostObservation(disk_pct=disk))
    evidence = QueueEventEvidence(0, stamp, ((SCOPE, (1, 2, 1, 3), tuple(
        ("order_expired", digest) for digest in digests
    )),))
    return WatchCycleResult(report, (), evidence, ((SCOPE, "complete", "complete"),))


def run(fd, observed, send, request=REQUEST):
    return deliver_summary(request, fd, observed, cfg={}, deadline=40, send=send)


def test_all_93_pending_conditions_use_one_post_and_one_ack(cursor):
    fd, _ = cursor
    names = _account_names(_policy(RELEASE))
    accounts = {scope: AccountObservation(601, 601, True, 10, 5, False, True, True, 121, 61) for scope in names}
    report = assess_group_a_watch(RELEASE, accounts=accounts, host=HostObservation(81, 86, True))
    def observed(stamp):
        return WatchCycleResult(report, (), QueueEventEvidence(0, stamp, tuple(
            (scope, (1, i * 2 + 1, 2, i * 2 + 2), (("order_expired", "a" * 64), ("order_refused", "b" * 64)))
            for i, scope in enumerate(names)
        )), tuple((scope, "complete", "complete") for scope in names))
    sent = []
    def send(release, stamp, findings, health, mask, **kwargs):
        sent.append(json.loads(summary_body(release, stamp, findings, health, mask)))
        return True
    assert run(fd, observed(1), send)["outcome"] == "slack_accepted"
    assert len(sent) == 1 and len(json.loads(sent[0]["text"].split("\n", 1)[1])["findings"]) == 93
    assert run(fd, observed(2), lambda *a, **kw: pytest.fail("duplicate post"))["outcome"] == "idle"


def test_new_staging_capacity_does_not_strand_old_pending(cursor, monkeypatch):
    fd, _ = cursor
    monkeypatch.setattr(legacy, "_EVENT_CAP", 1)
    assert run(fd, observation(1, ("a" * 64,)), lambda *a, **kw: False)["outcome"] == "unconfirmed"
    calls = []
    def accepted(release, stamp, findings, health, mask, **kwargs):
        calls.append(findings)
        assert health.present & bit_for(RELEASE, "cursor_capacity")
        assert all(row[2] == 1 for row in findings)
        return True
    result = run(fd, observation(2, ("a" * 64, "b" * 64)), accepted)
    assert result["present"] & bit_for(RELEASE, "cursor_capacity") and len(calls) == 1
    with image.open_group_a_cursor_image(fd) as connection:
        assert connection.execute("SELECT COUNT(*) FROM delivery_queue_event").fetchone() == (1,)
        assert connection.execute("SELECT observed_ms FROM delivery_cycle").fetchone() == (1,)
        assert connection.execute("SELECT COUNT(*) FROM delivery_finding WHERE pending=1").fetchone() == (0,)


def test_stage_persistence_uncertainty_does_not_overwrite_new_image(cursor, monkeypatch):
    fd, root = cursor
    run(fd, observation(1), lambda *a, **kw: False)
    original = image._ImageConnection.commit
    def fail_after_replace(connection):
        original(connection)
        raise OSError("synthetic post-replace fsync uncertainty")
    monkeypatch.setattr(image._ImageConnection, "commit", fail_after_replace)
    saved = []
    def accepted(*args, **kwargs):
        saved.append((root / image.IMAGE_NAME).read_bytes())
        return True
    result = run(fd, observation(2), accepted)
    assert result["present"] & bit_for(RELEASE, "cursor_unavailable")
    assert result["outcome"] == "fault" and result["acknowledged"] == 0
    assert len(saved) == 1 and (root / image.IMAGE_NAME).read_bytes() == saved[0]


def test_ack_failure_remains_pending_and_replays(cursor, monkeypatch):
    fd, _ = cursor
    original = image._ImageConnection.commit
    counter = [0]
    def fail_ack(connection):
        counter[0] += 1
        if counter[0] == 2:
            raise OSError("synthetic acknowledgement failure")
        return original(connection)
    monkeypatch.setattr(image._ImageConnection, "commit", fail_ack)
    assert run(fd, observation(1), lambda *a, **kw: True)["outcome"] == "unconfirmed"
    monkeypatch.setattr(image._ImageConnection, "commit", original)
    assert run(fd, observation(2), lambda *a, **kw: True)["outcome"] == "slack_accepted"


@pytest.mark.parametrize("damage", ["missing", "corrupt", "symlink"])
def test_unavailable_cursor_sends_only_health_and_never_initializes(cursor, damage):
    fd, root = cursor
    target = root / image.IMAGE_NAME
    target.unlink()
    if damage == "corrupt":
        target.write_bytes(b"not an image")
        target.chmod(0o600)
    elif damage == "symlink":
        outside = root.parent / "outside"
        outside.write_bytes(image.EMPTY_IMAGE)
        outside.chmod(0o600)
        target.symlink_to(outside)
    calls = []
    def send(release, stamp, findings, health, mask, **kwargs):
        assert findings == () and mask & bit_for(RELEASE, "cursor_unavailable")
        calls.append(mask)
        return True
    result = run(fd, observation(1), send)
    assert len(calls) == 1 and result["present"] & bit_for(RELEASE, "cursor_unavailable")
    assert result["unknown"] & bit_for(RELEASE, "cursor_capacity")
    if damage == "missing":
        assert not target.exists()


def test_wrong_release_or_stale_cycle_cannot_send(cursor):
    fd, _ = cursor
    run(fd, observation(2), lambda *a, **kw: True)
    for request in (REQUEST, control("another42", "a" * 32, 0)):
        with pytest.raises(ValueError):
            run(fd, observation(1), lambda *a, **kw: pytest.fail("bad cycle sent"), request=request)


def test_source_health_unknown_is_not_a_recovery(cursor):
    fd, _ = cursor
    current = observation(1, disk=0)
    current = WatchCycleResult(current.report, (), current.queue_events, ((SCOPE, "unavailable", "unknown"),))
    result = run(fd, current, lambda *a, **kw: True)
    assert result["present"] & bit_for(RELEASE, "source_copy_unavailable", SCOPE)
    assert result["unknown"] & bit_for(RELEASE, "queue_evidence_limit", SCOPE)


def test_summary_never_uses_disk_sqlite(cursor, monkeypatch):
    fd, _ = cursor
    original = sqlite3.connect
    def connect(path, **kwargs):
        assert path == ":memory:"
        return original(path, **kwargs)
    monkeypatch.setattr(image.sqlite3, "connect", connect)
    assert run(fd, observation(1), lambda *a, **kw: True)["outcome"] == "slack_accepted"


def test_malformed_persisted_finding_is_health_only_not_a_reset(cursor):
    fd, root = cursor
    run(fd, observation(1), lambda *a, **kw: False)
    with image.open_group_a_cursor_image(fd) as connection:
        connection.execute("UPDATE delivery_finding SET first_seen_ms=-1")
        connection.commit()
    saved = (root / image.IMAGE_NAME).read_bytes()
    calls = []
    def send(release, stamp, findings, health, mask, **kwargs):
        assert findings == ()
        calls.append(mask)
        return True
    result = run(fd, observation(2), send)
    assert result["present"] & bit_for(RELEASE, "cursor_unavailable") and len(calls) == 1
    assert (root / image.IMAGE_NAME).read_bytes() == saved


def test_declared_image_limit_falls_back_to_old_pending(cursor, monkeypatch):
    fd, _ = cursor
    run(fd, observation(1), lambda *a, **kw: False)
    original = image._ImageConnection.commit
    calls = [0]
    def reject_stage(connection):
        calls[0] += 1
        if calls[0] == 1:
            raise ValueError("alert_cursor_image_capacity")
        return original(connection)
    monkeypatch.setattr(image._ImageConnection, "commit", reject_stage)
    sent = []
    result = run(fd, observation(2), lambda *args, **kw: sent.append(args[2]) or True)
    assert result["present"] & bit_for(RELEASE, "cursor_capacity")
    assert len(sent) == 1 and all(row[2] == 1 for row in sent[0])
