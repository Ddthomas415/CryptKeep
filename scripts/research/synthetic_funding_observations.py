"""Offline raw-funding adapter; caller-owned KV fixture, no production wiring."""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math


PREFIX = "synthetic_funding_observation:"


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def finite_number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def payload_interval(payload):
    info = payload.get("info")
    info = info if isinstance(info, dict) else {}
    fields = {
        "interval": payload.get("interval"),
        "interval_hours": payload.get("interval_hours"),
        "fundingIntervalHours": payload.get("fundingIntervalHours"),
        "info.fundingIntervalHours": info.get("fundingIntervalHours"),
    }
    values = {}
    for name, value in fields.items():
        if value is None:
            continue
        if name == "interval":
            value = value[:-1] if isinstance(value, str) and value.endswith("h") else None
        number = finite_number(value)
        if number is None or number <= 0:
            return None, [], "interval_invalid"
        values[name] = number
    if not values:
        return None, [], "interval_unknown"
    if len(set(values.values())) != 1:
        return None, [], "interval_conflict"
    return next(iter(values.values())), list(values), None


def observation(*, venue, symbol, captured_at, payload, plan_interval_hours=None):
    """Keep raw evidence. Provider field names do not authenticate semantics."""
    if any(type(value) is not str or not value.strip() for value in (venue, symbol, captured_at)):
        raise ValueError("explicit_identity_and_capture_time_required")
    parsed = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone_required")
    if not isinstance(payload, dict):
        raise ValueError("json_object_required")
    # Roundtrip rejects unsupported objects/non-finite JSON and isolates callers.
    raw = json.loads(encoded(payload))
    encoded(plan_interval_hours)
    info = raw.get("info")
    info = info if isinstance(info, dict) else {}
    fields = [(name, raw.get(name)) for name in
              ("fundingRate", "funding_rate", "nextFundingRate", "next_funding_rate")]
    fields += [("info." + name, info.get(name)) for name in
               ("fundingRate", "funding_rate", "nextFundingRate", "next_funding_rate")]
    rate, source = None, None
    for name, value in fields:
        number = finite_number(value)
        if number is not None:
            rate, source = number, name
            break
    interval, interval_fields, interval_reason = payload_interval(raw)
    kind = "predicted" if source and "next" in source.lower() else "unknown"
    reason = "rate_unknown" if rate is None else interval_reason or "formula_basis_unverified"
    times = {name: raw[name] for name in
             ("timestamp", "datetime", "fundingTimestamp", "fundingDatetime",
              "nextFundingTimestamp", "nextFundingDatetime") if name in raw}
    times.update({"info." + name: info[name] for name in
                  ("timestamp", "ts", "fundingTime", "nextFundingTime") if name in info})
    return {
        "schema": 1, "venue": venue, "symbol": symbol, "captured_at": captured_at,
        "raw_payload": raw, "funding_rate": rate, "rate_source_field": source,
        "rate_kind": kind, "rate_kind_verified": False,
        "interval_hours": interval, "interval_source_fields": interval_fields,
        "interval_issue": interval_reason, "plan_interval_hours_unverified": plan_interval_hours,
        "reported_exchange_time_fields": times, "formula_version": "unverified",
        "normalization": {"eligible": False, "reason": reason,
                          "rate_per_8h": None, "annualized_pct": None},
        "execution_authority": False,
    }


def identity(record):
    return PREFIX + hashlib.sha256(encoded(record).encode()).hexdigest()


def append_observation(connection, *, max_bytes, **inputs):
    """Append to an explicitly pre-created disposable live_consumer_state fixture.

    No DDL, DB paths, initialization, overwrite, deletion or release mechanism.
    Own the transaction; callers must not pass an active transaction.
    """
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("explicit_positive_byte_budget_required")
    if connection.in_transaction:
        raise ValueError("caller_transaction_active")
    record = observation(**inputs)
    body = encoded(record)
    if len(body.encode()) > max_bytes:
        raise ValueError("observation_byte_budget_exceeded")
    key = identity(record)
    began = False
    try:
        connection.execute("BEGIN IMMEDIATE")
        began = True
        existing = connection.execute("SELECT v FROM live_consumer_state WHERE k=?", (key,)).fetchone()
        if existing is None:
            connection.execute("INSERT INTO live_consumer_state(k,v) VALUES(?,?)", (key, body))
        elif existing[0] != body:
            raise ValueError("stored_observation_conflict")
        connection.commit()
        began = False
        return {"key": key, "inserted": existing is None, "observation": deepcopy(record)}
    finally:
        if began:
            connection.rollback()


def read_observation(connection, key):
    if not isinstance(key, str) or not key.startswith(PREFIX):
        raise ValueError("observation_key_required")
    row = connection.execute("SELECT v FROM live_consumer_state WHERE k=?", (key,)).fetchone()
    if row is None:
        raise ValueError("observation_missing")
    record = json.loads(row[0])
    if not isinstance(record, dict) or record.get("schema") != 1 or identity(record) != key:
        raise ValueError("stored_observation_corrupt")
    return record
