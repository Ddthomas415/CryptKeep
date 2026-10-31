"""Disposable SQLite checkpoint prototype. No DB locator, DDL or order authority."""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import sqlite3

from services.execution.exit_deferral import ExitPolicy, plan_exit


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def key_for(bucket):
    if (type(bucket) not in (list, tuple) or len(bucket) != 3 or bucket[0] != "coinbase"
            or any(type(value) is not str or not value.strip() for value in bucket)):
        raise ValueError("explicit_venue_account_intent_bucket_required")
    return "synthetic_exit_checkpoint:" + encoded(list(bucket))


def initial_fixture_state(bucket, intent, policy):
    """Return test seed data only; never create or initialize a database row."""
    key_for(bucket)
    if not isinstance(policy, ExitPolicy) or intent["intent_id"] != bucket[2]:
        raise ValueError("fixture_identity_or_policy_mismatch")
    progress = {name: intent[name] for name in ("intent_id", "venue", "product_id")}
    progress.update(attempts=0, last_attempt_ms=None, outcome="never_submitted", confirmed_filled_quantity="0")
    plan_exit(intent, None, progress, now_ms=0, policy=policy)
    return {"schema": 1, "bucket": list(bucket), "intent": deepcopy(intent), "policy": asdict(policy),
            "progress": progress, "revision": 0, "last_ms": None, "reservation": None, "alerts": {}}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_state_key")
        result[key] = value
    return result


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("invalid_state_integer")
    return value


def validate(state, bucket, policy, now):
    if (not isinstance(state, dict) or set(state) != {"schema", "bucket", "intent", "policy", "progress",
            "revision", "last_ms", "reservation", "alerts"}
            or type(state["schema"]) is not int or state["schema"] != 1
            or state["bucket"] != list(bucket) or state["policy"] != asdict(policy)
            or state["intent"]["intent_id"] != bucket[2] or not isinstance(state["alerts"], dict)):
        raise ValueError("state_scope_schema_or_policy_mismatch")
    revision = integer(state["revision"])
    if revision == 0:
        if state != initial_fixture_state(bucket, state["intent"], policy):
            raise ValueError("corrupt_initial_fixture")
    elif integer(state["last_ms"]) > now:
        raise ValueError("regressed_checkpoint_clock")
    reservation = state["reservation"]
    if reservation is not None:
        if (not isinstance(reservation, dict) or set(reservation) != {"token", "attempt", "claimed_at_ms", "revision"}
                or integer(reservation["revision"]) == 0 or reservation["revision"] > revision
                or type(reservation["attempt"]) is not int or reservation["attempt"] != state["progress"]["attempts"]
                or reservation["claimed_at_ms"] != state["progress"]["last_attempt_ms"]
                or state["progress"]["outcome"] not in ("unknown", "open")
                or reservation["token"] != digest([list(bucket), state["intent"], reservation["revision"],
                                                   reservation["attempt"], reservation["claimed_at_ms"]])):
            raise ValueError("unresolved_reservation_corrupt")
    for identity, alert in state["alerts"].items():
        if (not isinstance(alert, dict) or set(alert) != {"event", "attempt", "first_recorded_ms"}
                or integer(alert["first_recorded_ms"]) > now
                or integer(alert["attempt"]) > state["progress"]["attempts"]
                or alert["event"].get("intent_id") != bucket[2]
                or alert["event"].get("product_id") != state["intent"]["product_id"]
                or alert["event"].get("delivery_verified") is not False
                or identity != digest([list(bucket), alert["event"], alert["attempt"]])):
            raise ValueError("corrupt_alert_evidence")


def checkpoint(connection, *, bucket, observation, now_ms, policy, max_state_bytes):
    """Atomically plan/reserve in an explicitly seeded caller-owned fixture.

    Counts conservative reservations, not observed exchange submissions. There
    is deliberately no release/reconciliation API or timeout-based reset.
    """
    began = False
    try:
        key = key_for(bucket)
        now = integer(now_ms)
        if not isinstance(policy, ExitPolicy) or integer(max_state_bytes) == 0:
            raise ValueError("explicit_policy_and_state_budget_required")
        if connection.in_transaction:
            raise ValueError("unowned_transaction")
        connection.execute("BEGIN IMMEDIATE")
        began = True
        row = connection.execute("SELECT v FROM live_consumer_state WHERE k=?", (key,)).fetchone()
        if row is None or type(row[0]) is not str or len(row[0].encode()) > max_state_bytes:
            raise ValueError("state_missing_or_over_budget")
        state = json.loads(row[0], object_pairs_hook=unique_object)
        validate(state, bucket, policy, now)
        result = plan_exit(state["intent"], observation, state["progress"], now_ms=now, policy=policy)
        state["revision"] += 1
        state["last_ms"] = now
        if result["status"] == "ELIGIBLE_FOR_EXISTING_GATES":
            progress = state["progress"]
            progress.update(attempts=progress["attempts"] + 1, last_attempt_ms=now, outcome="unknown")
            reservation = {"attempt": progress["attempts"], "claimed_at_ms": now, "revision": state["revision"]}
            reservation["token"] = digest([list(bucket), state["intent"], reservation["revision"],
                                            reservation["attempt"], now])
            state["reservation"] = reservation
            result["status"] = "RESERVED_OFFLINE_ONLY"
            result["reason"] = "conservative_reservation_requires_existing_gates"
        event = result["alert_event"]
        if event is not None:
            attempt = state["progress"]["attempts"]
            identity = digest([list(bucket), event, attempt])
            state["alerts"].setdefault(identity, {"event": deepcopy(event), "attempt": attempt, "first_recorded_ms": now})
        payload = encoded(state)
        if len(payload.encode()) > max_state_bytes:
            raise ValueError("updated_state_over_budget")
        cursor = connection.execute("UPDATE live_consumer_state SET v=? WHERE k=? AND v=?", (payload, key, row[0]))
        if cursor.rowcount != 1:
            raise ValueError("checkpoint_write_not_confirmed")
        connection.execute("COMMIT")
        began = False
        result.update(reservation=deepcopy(state["reservation"]), checkpoint_progress=deepcopy(state["progress"]),
                      revision=state["revision"], recorded_alert_count=len(state["alerts"]))
        return result
    except (ValueError, TypeError, KeyError, AttributeError, sqlite3.Error):
        return {"status": "INCOMPLETE", "reason": "checkpoint_evidence_or_store_failure",
                "request": None, "execution_authority": False, "evidence_authenticated": False}
    finally:
        if began and connection.in_transaction:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                raise RuntimeError("checkpoint_owned_rollback_failed") from None
