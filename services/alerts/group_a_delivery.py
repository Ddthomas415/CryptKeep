"""Persist watcher findings before sending; no queue, service or credential access."""

from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from services.alerts.group_a_watch import (
    WatchFinding, WatchReport, _ACCOUNT_RULES, _HOST_RULES, _account_names, _policy,
    dispatch_group_a_alert,
)
from services.alerts.group_a_watch_cycle import QueueEventEvidence
from services.alerts.group_a_cursor_image import open_group_a_cursor_image
from services.alerts.group_a_cursor_schema import SCHEMA


_QUEUE_CODES = ("order_expired", "order_refused")
_EVENT_CAP = 16_384


@dataclass(frozen=True)
class DeliveryAttempt:
    finding: WatchFinding | None
    outcome: str


class DeliveryUnconfirmed(RuntimeError):
    """A send may have happened, but its local acknowledgement is not proven."""


def _findings(values, allowed):
    if type(values) is not tuple or len(values) > len(allowed):
        raise ValueError("invalid_group_a_delivery_report")
    result = set()
    for finding in values:
        if (type(finding) is not WatchFinding or type(finding.scope) is not str
                or type(finding.code) is not str):
            raise ValueError("invalid_group_a_delivery_finding")
        key = (finding.scope, finding.code)
        if key not in allowed or key in result:
            raise ValueError("invalid_group_a_delivery_finding")
        result.add(key)
    return result


def _current_cycle(connection):
    return connection.execute("SELECT release, observed_ms FROM delivery_cycle WHERE id=1").fetchone()


def _stage_write(connection, statement, values):
    if connection.execute(statement, values).rowcount != 1:
        raise ValueError("group_a_delivery_stage_unconfirmed")


def _validated_events(evidence, names, observed_ms, active, unknown, *, event_cap=None):
    cap = _EVENT_CAP if event_cap is None else event_cap
    if type(cap) is not int or not 0 < cap <= 9 * 3 * 4096:
        raise ValueError("invalid_group_a_queue_evidence_cap")
    if evidence is None:
        return None
    if (type(evidence) is not QueueEventEvidence or type(evidence.since_ms) is not int
            or type(evidence.observed_ms) is not int or evidence.observed_ms != observed_ms
            or not 0 <= evidence.since_ms < observed_ms or type(evidence.accounts) is not tuple
            or len(evidence.accounts) > len(names)):
        raise ValueError("invalid_group_a_queue_evidence")
    rows, covered = set(), {}
    for batch in evidence.accounts:
        if type(batch) is not tuple or len(batch) != 3:
            raise ValueError("invalid_group_a_queue_evidence")
        scope, identity, events = batch
        if (type(scope) is not str or scope not in names or scope in covered
                or type(identity) is not tuple or len(identity) != 4
                or any(type(n) is not int or not 0 <= n < 2**64 for n in identity)
                or not identity[1] or not identity[3]
                or type(events) is not tuple or len(events) > cap - len(rows)):
            raise ValueError("invalid_group_a_queue_evidence")
        covered[scope] = ":".join(map(str, identity))
        for event in events:
            if (type(event) is not tuple or len(event) != 2 or type(event[0]) is not str
                    or event[0] not in _QUEUE_CODES or type(event[1]) is not str
                    or len(event[1]) != 64 or re.fullmatch(r"[a-f0-9]{64}", event[1]) is None
                    or (scope, *event) in rows):
                raise ValueError("invalid_group_a_queue_evidence")
            rows.add((scope, *event))
    positive = {(scope, code) for scope, code, _ in rows}
    keys = {(scope, code) for scope in names for code in _QUEUE_CODES}
    if positive != (active & keys) or (unknown & keys) != {key for key in keys if key[0] not in covered}:
        raise ValueError("contradictory_group_a_queue_evidence")
    return evidence.since_ms, rows, covered


def _stage_events(connection, events, previous):
    connection.execute(SCHEMA["epoch"])
    epoch = connection.execute("SELECT since_ms FROM delivery_queue_epoch WHERE id=1").fetchone()
    if events is None:
        if epoch is not None:
            raise ValueError("group_a_queue_evidence_required")
        return set()
    since_ms, rows, covered = events
    if epoch != (since_ms,):
        if previous is not None or epoch is not None:
            raise ValueError("wrong_group_a_queue_evidence_epoch")
        _stage_write(connection, "INSERT INTO delivery_queue_epoch VALUES (1, ?)", (since_ms,))
    connection.execute(SCHEMA["source"])
    for scope, identity in covered.items():
        prior = connection.execute("SELECT identity FROM delivery_queue_source WHERE scope=?", (scope,)).fetchone()
        if prior is None:
            _stage_write(connection, "INSERT INTO delivery_queue_source VALUES (?, ?)", (scope, identity))
        elif prior != (identity,):
            raise ValueError("group_a_queue_evidence_source_changed")
    connection.execute(SCHEMA["event"])
    stored = set(connection.execute("SELECT scope, code, digest FROM delivery_queue_event LIMIT ?", (_EVENT_CAP + 1,)))
    novel = rows - stored
    if len(stored) + len(novel) > _EVENT_CAP:
        raise ValueError("group_a_queue_evidence_capacity")
    for row in sorted(novel):
        _stage_write(connection, "INSERT INTO delivery_queue_event VALUES (?, ?, ?)", row)
    return {(scope, code) for scope, code, _ in novel}


def _stage(connection, release, observed_ms, active, unknown, events=None):
    connection.execute("BEGIN IMMEDIATE")
    connection.execute(SCHEMA["cycle"])
    connection.execute(SCHEMA["finding"])
    previous = _current_cycle(connection)
    if previous is not None and (previous[0] != release or observed_ms <= previous[1]):
        raise ValueError("stale_or_wrong_group_a_delivery_cycle")

    rearm = _stage_events(connection, events, previous)
    for key in active:
        if events is not None and key[1] in _QUEUE_CODES and key not in rearm:
            continue
        _stage_write(connection, """INSERT INTO delivery_finding VALUES (?, ?, 1, 1, ?, 0)
            ON CONFLICT(scope, code) DO UPDATE SET active=1
        """, (*key, observed_ms))
        if key in rearm:
            _stage_write(connection, """UPDATE delivery_finding
                SET pending=1, first_seen_ms=CASE WHEN pending=0 THEN ? ELSE first_seen_ms END,
                    last_attempt_ms=CASE WHEN pending=0 THEN 0 ELSE last_attempt_ms END
                WHERE scope=? AND code=?""", (observed_ms, *key))
    for scope, code, pending in connection.execute("SELECT scope, code, pending FROM delivery_finding").fetchall():
        key = scope, code
        if key not in active and key not in unknown:
            if pending:
                _stage_write(connection, "UPDATE delivery_finding SET active=0 WHERE scope=? AND code=?", key)
            else:
                _stage_write(connection, "DELETE FROM delivery_finding WHERE scope=? AND code=?", key)
    _stage_write(connection, """INSERT INTO delivery_cycle VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET observed_ms=excluded.observed_ms
    """, (release, observed_ms))
    if _current_cycle(connection) != (release, observed_ms):
        raise ValueError("group_a_delivery_stage_unconfirmed")
    connection.commit()


def deliver_group_a_cycle(path: Path, release: str, report: WatchReport, *, observed_ms: int, cfg, send_alert,
                          queue_events: QueueEventEvidence | None = None):
    """Stage one fresh report and attempt at most one pending Slack notification.

    The caller owns and provisions the protected, local cursor directory, separate
    from watched queues, and supplies a bounded sender. Quiet rearms acknowledged
    conditions; unknown does not. Unsent episodes for the same finding coalesce.
    An external acceptance followed by a crash can repeat. This is not a queue
    history watermark, terminal-hook sender, or owner receipt. A fresh cursor
    can track retained queue evidence at a fixed lower bound. New identities
    rearm delivery, and pending evidence for the same finding can coalesce.
    """
    if (type(path) is not type(Path()) or not path.is_absolute() or ".." in path.parts
            or path.name != "group_a_delivery.sqlite"):
        raise ValueError("invalid_group_a_delivery_input")
    return _deliver_cycle(lambda: _file_connection(path), release, report, observed_ms=observed_ms,
                          cfg=cfg, send_alert=send_alert, queue_events=queue_events)


@contextmanager
def _file_connection(path):
    with closing(sqlite3.connect(path, timeout=0)) as connection, connection:
        if connection.execute("PRAGMA journal_mode").fetchone() != ("delete",):
            raise ValueError("unexpected_group_a_cursor_journal_mode")
        connection.execute("PRAGMA synchronous=EXTRA")
        yield connection


def deliver_group_a_image_cycle(directory_fd, release, report, *, observed_ms, cfg, send_alert, queue_events):
    """Use a protected directory FD; the durable image is not a SQLite pathname."""
    return _deliver_cycle(lambda: open_group_a_cursor_image(directory_fd), release, report, observed_ms=observed_ms,
                          cfg=cfg, send_alert=send_alert, queue_events=queue_events)


def _deliver_cycle(open_connection, release, report, *, observed_ms, cfg, send_alert, queue_events):
    policy = _policy(release)
    if (type(report) is not WatchReport or type(observed_ms) is not int
            or not 0 < observed_ms <= 253_402_300_799_999 or not callable(send_alert)):
        raise ValueError("invalid_group_a_delivery_input")
    names = _account_names(policy)
    allowed = {(scope, rule[1]) for scope in names for rule in _ACCOUNT_RULES}
    allowed.update((policy.target, rule[1]) for rule in _HOST_RULES)
    active = _findings(report.alerts, allowed)
    unknown = _findings(report.missing, allowed)
    if active & unknown:
        raise ValueError("contradictory_group_a_delivery_report")
    events = _validated_events(queue_events, names, observed_ms, active, unknown)

    with open_connection() as connection:
        _stage(connection, release, observed_ms, active, unknown, events)
        # Hold the writer reservation through the one send so another process
        # cannot submit the same row before the acknowledgement is committed.
        connection.execute("BEGIN IMMEDIATE")
        current = _current_cycle(connection)
        if current != (release, observed_ms):
            if current is not None and current[0] == release and current[1] > observed_ms:
                return DeliveryAttempt(None, "superseded")
            raise ValueError("group_a_delivery_stage_unconfirmed")
        row = connection.execute("""SELECT scope, code, active, first_seen_ms, last_attempt_ms FROM delivery_finding
            WHERE pending=1 ORDER BY last_attempt_ms, scope, code LIMIT 1
        """).fetchone()
        if row is None:
            return DeliveryAttempt(None, "idle")
        key = row[:2]
        finding = WatchFinding(*key)

        def send_with_timestamp(*, payload, **kwargs):
            return send_alert(payload={**payload, "first_observed_ms": row[3]}, **kwargs)

        try:
            outcome = dispatch_group_a_alert(release, finding, cfg=cfg, send_alert=send_with_timestamp)
            if outcome == "slack_accepted":
                if row[2]:
                    connection.execute("UPDATE delivery_finding SET pending=0 WHERE scope=? AND code=?", key)
                    expected = (0, row[4])
                else:
                    connection.execute("DELETE FROM delivery_finding WHERE scope=? AND code=?", key)
                    expected = None
            else:
                connection.execute("""UPDATE delivery_finding SET last_attempt_ms=MAX(last_attempt_ms, ?)
                    WHERE scope=? AND code=?""", (observed_ms, *key))
                expected = (1, max(row[4], observed_ms))
            stored = connection.execute("""SELECT pending, last_attempt_ms FROM delivery_finding
                WHERE scope=? AND code=?""", key).fetchone()
            if stored != expected:
                raise DeliveryUnconfirmed("group_a_alert_acknowledgement_unconfirmed")
            connection.commit()
        except (sqlite3.Error, OSError, ValueError):
            raise DeliveryUnconfirmed("group_a_alert_acknowledgement_unconfirmed") from None
        return DeliveryAttempt(finding, outcome)
