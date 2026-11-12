"""Image-backed summary delivery; never discard pending evidence to make room."""

import sqlite3

from services.alerts import group_a_cursor_image as image
from services.alerts import group_a_delivery as legacy
from services.alerts.group_a_summary_protocol import (
    Health, _account_names, _policy, bit_for, cycle_result, encode_control, summary_body,
)
from services.alerts.group_a_summary_transport import send_summary
from services.alerts.group_a_watch_cycle import QueueEventEvidence, WatchCycleResult


def _source_health(release, coverage):
    health = Health()
    names = set(_account_names(_policy(release)))
    seen = set()
    if type(coverage) is not tuple or len(coverage) > len(names):
        raise ValueError("invalid_group_a_source_coverage")
    for row in coverage:
        if type(row) is not tuple or len(row) != 3:
            raise ValueError("invalid_group_a_source_coverage")
        scope, copied, adapter = row
        if (type(scope) is not str or scope not in names or scope in seen
                or copied not in ("complete", "unavailable")
                or adapter not in ("complete", "limit", "unknown")
                or copied == "unavailable" and adapter != "unknown"):
            raise ValueError("invalid_group_a_source_coverage")
        seen.add(scope)
        health = health.with_state(bit_for(release, "source_copy_unavailable", scope),
                                   "known_clear" if copied == "complete" else "present")
        health = health.with_state(bit_for(release, "queue_evidence_limit", scope),
                                   {"complete": "known_clear", "limit": "present", "unknown": "unknown"}[adapter])
    return health


def _pending(connection, allowed, observed_ms):
    rows = connection.execute("""SELECT scope, code, active, pending, first_seen_ms, last_attempt_ms
        FROM delivery_finding ORDER BY scope, code LIMIT 94""").fetchall()
    if len(rows) > 93:
        raise ValueError("invalid_group_a_pending_snapshot")
    pending = []
    for scope, code, active, needed, first, last in rows:
        if (type(scope) is not str or type(code) is not str or (scope, code) not in allowed
                or type(active) is not int or active not in (0, 1)
                or type(needed) is not int or needed not in (0, 1)
                or type(first) is not int or not 0 < first <= observed_ms
                or type(last) is not int or not 0 <= last <= observed_ms):
            raise ValueError("invalid_group_a_pending_snapshot")
        if needed:
            pending.append((scope, code, first))
    return tuple(pending)


def _acknowledge(connection, findings):
    connection.execute("BEGIN IMMEDIATE")
    for scope, code, first in findings:
        row = connection.execute("SELECT active, pending, first_seen_ms FROM delivery_finding WHERE scope=? AND code=?",
                                 (scope, code)).fetchone()
        if row not in ((0, 1, first), (1, 1, first)):
            raise ValueError("group_a_summary_ack_unconfirmed")
        if row[0]:
            legacy._stage_write(connection, "UPDATE delivery_finding SET pending=0 WHERE scope=? AND code=?",
                                (scope, code))
        else:
            legacy._stage_write(connection, "DELETE FROM delivery_finding WHERE scope=? AND code=?", (scope, code))
    connection.commit()


def deliver_summary(request, directory_fd, observation, *, cfg, deadline, send=send_summary):
    encode_control(request)
    release = request["release"]
    if (type(observation) is not WatchCycleResult or type(observation.queue_events) is not QueueEventEvidence):
        raise ValueError("tracked_group_a_observation_required")
    stamp = observation.queue_events.observed_ms
    policy = _policy(release)
    names = _account_names(policy)
    from services.alerts.group_a_watch import WatchReport, _ACCOUNT_RULES, _HOST_RULES
    if type(observation.report) is not WatchReport:
        raise ValueError("invalid_group_a_summary_report")
    allowed = {(name, rule[1]) for name in names for rule in _ACCOUNT_RULES}
    allowed.update((policy.target, rule[1]) for rule in _HOST_RULES)
    active = legacy._findings(observation.report.alerts, allowed)
    unknown = legacy._findings(observation.report.missing, allowed)
    if active & unknown:
        raise ValueError("contradictory_group_a_summary_report")
    # Validate a bounded producer batch even when it cannot fit the durable
    # ledger, so already-pending evidence can still be delivered on overflow.
    events = legacy._validated_events(observation.queue_events, names, stamp, active, unknown,
                                      event_cap=9 * 3 * 4096)
    health = _source_health(release, observation.queue_health)
    # Validate the clock/roster before attempting either the cursor or network.
    summary_body(release, stamp, (), health, 0)

    def transmit(pending, current, fatal=False, acknowledge=None):
        eligible = current.present & ~request["suppressed"]
        outcome, ack = "idle", 0
        if pending or eligible:
            summary_body(release, stamp, pending, current, eligible)
            accepted = send(release, stamp, pending, current, eligible, cfg=cfg, deadline=deadline)
            outcome = "unconfirmed"
            if accepted is True:
                try:
                    if acknowledge is not None and pending:
                        acknowledge(pending)
                    if not pending or acknowledge is not None:
                        outcome, ack = "slack_accepted", eligible
                except (OSError, ValueError, sqlite3.Error):
                    outcome = "unconfirmed"
        return cycle_result(request, stamp, outcome if not fatal or outcome == "slack_accepted" else "fault",
                            current, ack)

    cursor_opened = False
    try:
        with image.open_group_a_cursor_image(directory_fd) as connection:
            cursor_opened = True
            try:
                snapshot = connection.checkpoint()
                previous = legacy._current_cycle(connection)
            except (ValueError, sqlite3.Error, OSError):
                health = health.with_state(bit_for(release, "cursor_unavailable"), "present")
                return transmit((), health, fatal=True)
            if previous is not None and (previous[0] != release or stamp <= previous[1]):
                raise ValueError("stale_or_wrong_group_a_delivery_cycle")
            try:
                old = _pending(connection, allowed, stamp)
            except (ValueError, sqlite3.Error, OSError):
                health = health.with_state(bit_for(release, "cursor_unavailable"), "present")
                return transmit((), health, fatal=True)
            health = health.with_state(bit_for(release, "cursor_unavailable"), "known_clear")
            fatal = False
            try:
                legacy._stage(connection, release, stamp, active, unknown, events)
            except (ValueError, sqlite3.Error, OSError) as error:
                capacity = (type(error) is ValueError and str(error) in (
                    "group_a_queue_evidence_capacity", "alert_cursor_image_capacity",
                )) or (isinstance(error, sqlite3.Error) and getattr(error, "sqlite_errorcode", None) == sqlite3.SQLITE_FULL)
                if not capacity:
                    # An uncertain replacement must never be overwritten with the old snapshot.
                    health = health.with_state(bit_for(release, "cursor_unavailable"), "present")
                    return transmit(old, health, fatal=True)
                connection.restore(snapshot)
                health = health.with_state(bit_for(release, "cursor_capacity"), "present")
                fatal = True
                pending = old
            else:
                pending = _pending(connection, allowed, stamp)
                health = health.with_state(bit_for(release, "cursor_capacity"), "known_clear")
            count, = connection.execute("SELECT COUNT(*) FROM delivery_queue_event").fetchone()
            near = count >= legacy._EVENT_CAP * 3 // 4 or connection.image_bytes >= image._MAX_IMAGE * 3 // 4
            health = health.with_state(bit_for(release, "cursor_near_capacity"), "present" if near else "known_clear")
            result = transmit(pending, health, fatal, lambda rows: _acknowledge(connection, rows))
            # Fatal status is conveyed independently of successful health delivery.
            return result
    except (OSError, sqlite3.Error, ValueError):
        if cursor_opened:
            raise
        health = health.with_state(bit_for(release, "cursor_unavailable"), "present")
        return transmit((), health, fatal=True)
