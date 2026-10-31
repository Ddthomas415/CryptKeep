"""Synthetic cap prototype; no production imports, schema creation or order authority."""

import asyncio
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json
import sqlite3


class EvidenceError(ValueError):
    pass


def number(value, *, positive=False):
    if type(value) not in (str, int):
        raise EvidenceError("invalid_number")
    try:
        decimal = Decimal(value)
        if not decimal.is_finite():
            raise EvidenceError("invalid_number")
        result = Fraction(decimal)
    except (InvalidOperation, ValueError, OverflowError):
        raise EvidenceError("invalid_number") from None
    if result < 0 or (positive and result == 0):
        raise EvidenceError("invalid_number")
    return result


def packed(value):
    return [value.numerator, value.denominator]


def unpacked(value, *, positive=False):
    if (not isinstance(value, list) or len(value) != 2
            or any(type(x) is not int for x in value) or value[0] < 0 or value[1] <= 0
            or (positive and value[0] == 0)):
        raise EvidenceError("corrupt_reservation")
    return Fraction(*value)


def bucket_key(bucket):
    if (not isinstance(bucket, (list, tuple)) or len(bucket) != 3
            or any(type(x) is not str or not x.strip() for x in bucket)):
        raise EvidenceError("verified_bucket_required")
    return "synthetic_cap:" + json.dumps(list(bucket), separators=(",", ":"))


def initial_fixture_state():
    """Caller must explicitly seed a disposable fixture; missing state never resets."""
    return {"schema": 1, "generation": None, "fingerprint": None,
            "clocks": None, "reservations": {}}


def answer(allow, reason, projected=None):
    return {"cap_allows": allow, "reason": reason,
            "projected_usd": None if projected is None else packed(projected),
            "execution_authority": False, "other_gates_required": True}


def clock(value):
    if type(value) is not int or value < 0:
        raise EvidenceError("invalid_clock")
    return value


def fresh(times, received, now, age, skew):
    now = now() if callable(now) else now
    now, age, skew, received = map(clock, (now, age, skew, received))
    times = [clock(x) for x in times]
    if (not times or any(t > received or t > now or now - t > age for t in times)
            or received > now or max(times) - min(times) > skew):
        raise EvidenceError("stale_future_or_skewed_evidence")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate_state_key")
        result[key] = value
    return result


def snapshot_evidence(snapshot, bucket, now, age, skew):
    if (not isinstance(snapshot, dict) or snapshot.get("bucket") != list(bucket)
            or any(snapshot.get(k) is not True for k in
                   ("identity_complete", "holdings_complete", "orders_complete", "fx_complete"))):
        raise EvidenceError("incomplete_snapshot")
    times = [snapshot[k] for k in ("holdings_ms", "orders_ms", "mark_ms", "fx_ms")]
    fresh(times, snapshot["received_ms"], now, age, skew)
    generation = clock(snapshot["generation"])
    held, mark = number(snapshot["held_units"]), number(snapshot["mark_usd"], positive=True)
    if (not isinstance(snapshot.get("included_fills"), dict)
            or not isinstance(snapshot.get("orders"), list)):
        raise EvidenceError("incomplete_snapshot")
    included = {k: number(v) for k, v in snapshot["included_fills"].items()}
    orders = {}
    for row in snapshot["orders"]:
        identity = row["id"]
        if type(identity) is not str or not identity or identity in orders:
            raise EvidenceError("duplicate_or_unknown_order_identity")
        original = number(row["original_units"], positive=True)
        filled, remaining = number(row["filled_units"]), number(row["remaining_units"])
        bound = number(row["unit_usd_bound"], positive=True)
        status = row["status"]
        if status not in ("queued", "submitting", "submitted", "held", "unknown",
                          "filled", "cancelled", "rejected"):
            raise EvidenceError("unknown_order_status")
        terminal = status in ("filled", "cancelled", "rejected")
        if (filled > original or included.get(identity, Fraction(0)) != filled
                or (terminal and remaining != 0)
                or (status == "filled" and filled != original)
                or (not terminal and remaining + filled != original)):
            raise EvidenceError("incoherent_fill_baseline")
        orders[identity] = {"original": packed(original), "filled": packed(filled),
                            "remaining": packed(remaining), "bound": packed(bound),
                            "terminal": terminal}
    fingerprint = hashlib.sha256(json.dumps(snapshot, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return held, mark, orders, generation, fingerprint, times


def admit(connection, *, bucket, proposal, snapshot, now_ms, max_age_ms,
          max_skew_ms, cap_usd, reduction=None):
    """Reserve an increase in a caller-owned disposable SQLite fixture.

    Identity/coverage are synthetic input assertions, not authenticated evidence.
    No table creation or order submission; only the prefixed KV row is changed.
    """
    began = False
    try:
        key = bucket_key(bucket)
        identity = proposal["id"]
        if (type(identity) is not str or not identity or proposal["base_asset_id"] != bucket[2]
                or type(proposal["quote_asset_id"]) is not str or not proposal["quote_asset_id"]):
            raise EvidenceError("invalid_proposal_identity")
        quantity = number(proposal["units"], positive=True)
        if proposal.get("spot_order") is not True:
            raise EvidenceError("spot_order_required")
        if proposal["side"] == "sell":
            if (not isinstance(reduction, dict) or reduction.get("bucket") != list(bucket)
                    or reduction.get("identity_complete") is not True
                    or reduction.get("pending_sells_complete") is not True):
                raise EvidenceError("reducing_evidence_required")
            fresh([reduction["as_of_ms"]], reduction["received_ms"],
                  now_ms, max_age_ms, max_skew_ms)
            if quantity + number(reduction["pending_sell_units"]) > number(reduction["held_units"]):
                raise EvidenceError("not_verified_reducing")
            return answer(True, "reducing_cap_only")
        if proposal["side"] != "buy":
            raise EvidenceError("unsupported_side")
        cap = number(cap_usd, positive=True)
        bound = number(proposal["unit_usd_bound"], positive=True)
        if proposal.get("bounded_spot_order") is not True:
            raise EvidenceError("bounded_spot_order_required")
        if connection.in_transaction:
            raise EvidenceError("unowned_transaction")
        connection.execute("BEGIN IMMEDIATE")
        began = True
        held, mark, orders, generation, fingerprint, times = snapshot_evidence(
            snapshot, bucket, now_ms, max_age_ms, max_skew_ms)
        row = connection.execute("SELECT v FROM live_consumer_state WHERE k=?", (key,)).fetchone()
        if row is None:
            raise EvidenceError("missing_reservation_state")
        state = json.loads(row[0], object_pairs_hook=unique_object)
        if (set(state) != {"schema", "generation", "fingerprint", "clocks", "reservations"}
                or type(state["schema"]) is not int or state["schema"] != 1
                or not isinstance(state["reservations"], dict)):
            raise EvidenceError("corrupt_state")
        if state["generation"] is not None:
            previous = clock(state["generation"])
            if (not isinstance(state["fingerprint"], str) or len(state["fingerprint"]) != 64
                    or any(x not in "0123456789abcdef" for x in state["fingerprint"])
                    or generation < previous
                    or (generation == previous and fingerprint != state["fingerprint"])
                    or len(state["clocks"]) != 4
                    or any(a < clock(b) for a, b in zip(times, state["clocks"]))):
                raise EvidenceError("regressed_snapshot")
        elif state != initial_fixture_state():
            raise EvidenceError("corrupt_initial_state")
        reservations = deepcopy(state["reservations"])
        for order_id, reserved in reservations.items():
            if set(reserved) != {"original", "filled", "remaining", "bound", "terminal"}:
                raise EvidenceError("corrupt_reservation")
            original = unpacked(reserved["original"], positive=True)
            filled = unpacked(reserved["filled"])
            remaining = unpacked(reserved["remaining"])
            old_bound = unpacked(reserved["bound"], positive=True)
            if (type(order_id) is not str or not order_id or type(reserved["terminal"]) is not bool
                    or filled + remaining > original or (reserved["terminal"] and remaining)
                    or (not reserved["terminal"] and filled + remaining != original)):
                raise EvidenceError("corrupt_reservation")
            observed = orders.get(order_id)
            if observed is None and number(snapshot["included_fills"].get(order_id, "0")) != filled:
                raise EvidenceError("retained_fill_baseline_unresolved")
            if observed is not None:
                observed["bound"] = packed(max(old_bound, unpacked(observed["bound"])))
                if (unpacked(observed["original"]) != original
                        or unpacked(observed["filled"]) < filled
                        or unpacked(observed["remaining"]) > remaining
                        or (reserved["terminal"] and observed != reserved)):
                    raise EvidenceError("regressed_order")
                reservations[order_id] = observed
        # Remember observed manual obligations too: absence is not terminal proof.
        for order_id, observed in orders.items():
            reservations.setdefault(order_id, observed)
        projected = held * mark + sum(
            unpacked(v["remaining"]) * max(mark, unpacked(v["bound"])) for v in reservations.values())
        projected += quantity * max(mark, bound)
        allowed = identity not in reservations and projected <= cap
        reason = "already_known_intent" if identity in reservations else (
            "reserved_cap_only" if allowed else "position_cap")
        if allowed:
            reservations[identity] = {"original": packed(quantity), "filled": [0, 1],
                                      "remaining": packed(quantity), "bound": packed(bound), "terminal": False}
        state.update(generation=generation, fingerprint=fingerprint, clocks=times, reservations=reservations)
        connection.execute("UPDATE live_consumer_state SET v=? WHERE k=?",
                           (json.dumps(state, sort_keys=True, allow_nan=False), key))
        connection.execute("COMMIT")
        began = False
        return answer(allowed, reason, projected)
    except (EvidenceError, KeyError, TypeError, ValueError, sqlite3.Error) as error:
        reason = str(error) if isinstance(error, EvidenceError) else "unreadable_evidence_or_store"
        return answer(False, reason)
    finally:
        if began:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass


async def admit_async(connection_factory, **kwargs):
    def work():
        connection = connection_factory()
        try:
            return admit(connection, **kwargs)
        finally:
            connection.close()
    try:
        return await asyncio.to_thread(work)
    except sqlite3.Error:
        return answer(False, "unreadable_evidence_or_store")
