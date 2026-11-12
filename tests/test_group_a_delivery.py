from contextlib import closing
import sqlite3
import subprocess
import sys

import pytest

from services.alerts import group_a_delivery as delivery
from services.alerts.group_a_watch import AccountObservation, HostObservation, WatchFinding, WatchReport, assess_group_a_watch
from services.alerts.group_a_watch_cycle import QueueEventEvidence


RELEASE = "frozen42"
SCOPE = "cbp-group-a-frozen42-breakout-default-btc"
EXPIRED = WatchFinding(SCOPE, "order_expired")
REFUSED = WatchFinding(SCOPE, "order_refused")
SLACK = {"ok": True, "channels": [{"channel": "slack", "ok": True, "status": 200}]}


@pytest.fixture
def path(tmp_path):
    return tmp_path.resolve() / "group_a_delivery.sqlite"


def run(path, when, *, alerts=(), missing=(), send=lambda **kw: SLACK, release=RELEASE):
    return delivery.deliver_group_a_cycle(
        path, release, WatchReport(alerts, missing), observed_ms=when, cfg={}, send_alert=send,
    )


def no_send(**_):
    pytest.fail("unexpected send")


def test_acknowledged_condition_rearms_only_after_known_clear(path):
    assert run(path, 1, alerts=(EXPIRED,)).outcome == "slack_accepted"
    assert run(path, 2, missing=(EXPIRED,), send=no_send).outcome == "idle"
    assert run(path, 3, alerts=(EXPIRED,), send=no_send).outcome == "idle"
    assert run(path, 4, send=no_send).outcome == "idle"
    assert run(path, 5, alerts=(EXPIRED,)).outcome == "slack_accepted"


@pytest.mark.parametrize("unverified", [
    {"ok": True, "skipped": True}, {"ok": True, "local_written": True},
    {"ok": True, "channels": [{"channel": "email", "ok": True}]},
])
def test_not_slack_accepted_stays_pending_even_after_quiet(path, unverified):
    assert run(path, 1, alerts=(EXPIRED,), send=lambda **kw: unverified).outcome == "external_unverified"

    def check(**kwargs):
        assert kwargs["payload"]["first_observed_ms"] == 1
        return SLACK

    assert run(path, 2, send=check).finding == EXPIRED
    assert run(path, 3, send=no_send).outcome == "idle"


def test_failed_finding_does_not_starve_other_pending_findings(path):
    def failed(**_):
        raise OSError("synthetic transport failure")

    assert run(path, 1, alerts=(EXPIRED, REFUSED), send=failed).outcome == "dispatch_failed"
    assert run(path, 2, alerts=(EXPIRED, REFUSED)).finding == REFUSED
    assert run(path, 3, alerts=(EXPIRED, REFUSED)).finding == EXPIRED
    assert run(path, 4, alerts=(EXPIRED, REFUSED), send=no_send).outcome == "idle"


def test_invalid_and_stale_cycles_cannot_send_or_clear(path):
    with pytest.raises(ValueError, match="contradictory"):
        run(path, 1, alerts=(EXPIRED,), missing=(EXPIRED,), send=no_send)
    with pytest.raises(ValueError, match="invalid_group_a_delivery_finding"):
        run(path, 1, alerts=(WatchFinding("elsewhere", "order_expired"),), send=no_send)
    assert not path.exists()
    run(path, 2, alerts=(EXPIRED,))
    for when, release in [(1, RELEASE), (2, RELEASE), (3, "another42")]:
        with pytest.raises(ValueError, match="stale_or_wrong"):
            run(path, when, release=release, send=no_send)
    assert run(path, 3, alerts=(EXPIRED,), send=no_send).outcome == "idle"


def test_concurrent_invocation_cannot_stage_or_send_during_dispatch(path):
    def competing(**_):
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            run(path, 2, alerts=(EXPIRED,), send=no_send)
        return SLACK

    assert run(path, 1, alerts=(EXPIRED,), send=competing).outcome == "slack_accepted"
    assert run(path, 2, alerts=(EXPIRED,), send=no_send).outcome == "idle"


def test_superseded_cycle_cannot_retry_newer_cycle_finding(path, monkeypatch):
    original = delivery._stage

    def stage_then_newer(*args):
        original(*args)
        if args[2] == 1:
            assert run(path, 2, alerts=(EXPIRED,), send=lambda **_: {}).outcome == "external_unverified"

    monkeypatch.setattr(delivery, "_stage", stage_then_newer)
    assert run(path, 1, send=no_send).outcome == "superseded"
    assert run(path, 3, missing=(EXPIRED,)).finding == EXPIRED


@pytest.mark.parametrize("target", ["cycle", "finding", "acknowledgement"])
def test_silently_ignored_cursor_write_cannot_claim_success(path, target):
    run(path, 1)
    event = {
        "cycle": "UPDATE ON delivery_cycle",
        "finding": "INSERT ON delivery_finding",
        "acknowledgement": "UPDATE OF pending ON delivery_finding",
    }[target]
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(f"CREATE TRIGGER ignore_write BEFORE {event} BEGIN SELECT RAISE(IGNORE); END")
    if target == "acknowledgement":
        with pytest.raises(delivery.DeliveryUnconfirmed):
            run(path, 2, alerts=(EXPIRED,))
    else:
        with pytest.raises(ValueError, match="stage_unconfirmed"):
            run(path, 2, alerts=(EXPIRED,), send=no_send)


def test_storage_abort_after_slack_acceptance_is_unconfirmed(path):
    run(path, 1)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("""CREATE TRIGGER fail_ack BEFORE UPDATE OF pending ON delivery_finding
            BEGIN SELECT RAISE(ABORT, 'synthetic ack failure'); END""")
    sent = []

    def accepted(**kwargs):
        sent.append(kwargs["payload"])
        return SLACK

    with pytest.raises(delivery.DeliveryUnconfirmed, match="acknowledgement_unconfirmed"):
        run(path, 2, alerts=(EXPIRED,), send=accepted)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("DROP TRIGGER fail_ack")
    assert run(path, 3, missing=(EXPIRED,), send=accepted).outcome == "slack_accepted"
    assert len(sent) == 2 and sent[0] == sent[1]


def test_storage_abort_before_dispatch_cannot_send(path):
    run(path, 1)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("""CREATE TRIGGER fail_stage BEFORE UPDATE ON delivery_cycle
            BEGIN SELECT RAISE(ABORT, 'synthetic stage failure'); END""")
    with pytest.raises(sqlite3.IntegrityError, match="synthetic stage failure"):
        run(path, 2, alerts=(EXPIRED,), send=no_send)
    with closing(sqlite3.connect(path)) as connection, connection:
        assert connection.execute("SELECT observed_ms FROM delivery_cycle").fetchone() == (1,)
        assert connection.execute("SELECT COUNT(*) FROM delivery_finding").fetchone() == (0,)


def test_process_exit_in_dispatch_leaves_durable_pending(path):
    code = '''
import os, sys
from pathlib import Path
from services.alerts.group_a_delivery import deliver_group_a_cycle
from services.alerts.group_a_watch import WatchFinding, WatchReport
finding = WatchFinding(sys.argv[2], "order_expired")
deliver_group_a_cycle(Path(sys.argv[1]), "frozen42", WatchReport((finding,), ()),
                      observed_ms=1, cfg={}, send_alert=lambda **kw: os._exit(23))
'''
    process = subprocess.run([sys.executable, "-B", "-c", code, str(path), SCOPE], timeout=5, check=False)
    assert process.returncode == 23
    assert run(path, 2, missing=(EXPIRED,)).finding == EXPIRED


def tracked(path, when, keys, *, since=0, identity=(1, 2, 1, 3), send=lambda **kw: SLACK):
    accounts = {} if keys is None else {SCOPE: AccountObservation(order_expired=bool(keys), order_refused=False)}
    report = assess_group_a_watch(RELEASE, accounts=accounts, host=HostObservation())
    evidence = QueueEventEvidence(since, when, () if keys is None else (
        (SCOPE, identity, tuple((EXPIRED.code, key) for key in keys)),
    ))
    return delivery.deliver_group_a_cycle(
        path, RELEASE, report, observed_ms=when, cfg={}, send_alert=send, queue_events=evidence,
    )


def test_retained_event_identity_survives_missing_and_disappearing_rows(path):
    a, b = "a" * 64, "b" * 64
    assert tracked(path, 1, (a,)).outcome == "slack_accepted"
    assert tracked(path, 2, None, send=no_send).outcome == "idle"
    assert tracked(path, 3, (), send=no_send).outcome == "idle"
    assert tracked(path, 4, (a,), send=no_send).outcome == "idle"
    assert tracked(path, 5, (a, b)).outcome == "slack_accepted"
    with pytest.raises(ValueError, match="wrong_group_a_queue_evidence_epoch"):
        tracked(path, 6, (a,), since=1, send=no_send)
    with pytest.raises(ValueError, match="group_a_queue_evidence_required"):
        run(path, 6, send=no_send)
    with pytest.raises(ValueError, match="group_a_queue_evidence_source_changed"):
        tracked(path, 6, (a,), identity=(1, 2, 1, 4), send=no_send)


def test_event_capacity_failure_preserves_pending_and_cycle(path, monkeypatch):
    a, b = "a" * 64, "b" * 64
    monkeypatch.setattr(delivery, "_EVENT_CAP", 1)
    assert tracked(path, 1, (a,), send=lambda **kw: {}).outcome == "external_unverified"
    with pytest.raises(ValueError, match="group_a_queue_evidence_capacity"):
        tracked(path, 2, (b,), send=no_send)
    assert tracked(path, 2, None).outcome == "slack_accepted"


def test_event_and_pending_stage_roll_back_together(path):
    a = "a" * 64
    assert tracked(path, 1, ()).outcome == "idle"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("""CREATE TRIGGER ignore_pending BEFORE INSERT ON delivery_finding
            BEGIN SELECT RAISE(IGNORE); END""")
    with pytest.raises(ValueError, match="stage_unconfirmed"):
        tracked(path, 2, (a,), send=no_send)
    with closing(sqlite3.connect(path)) as connection, connection:
        assert connection.execute("SELECT COUNT(*) FROM delivery_queue_event").fetchone() == (0,)
        connection.execute("DROP TRIGGER ignore_pending")
    assert tracked(path, 2, (a,)).outcome == "slack_accepted"
