"""Bounded R3 adapters for trusted offline queue copies and resource samples."""

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from itertools import islice
import json
import re
import sqlite3

from services.alerts.group_a_watch import HostObservation
from services.execution.paper_exit_retry import exit_identity, has_exit_marker
from storage.exit_event_journal import _decode_payload


MAX_SAMPLE_AGE_MS = 60_000
_ROW_CAP = 4096
_META_CAP = 32_768


class QueueEvidenceLimit(ValueError):
    """A known bounded-query limit, distinct from unreadable evidence."""


@dataclass(frozen=True, init=False)
class QueueSample:
    """A trusted producer's standalone, query-only in-memory SQLite copy."""

    connection: sqlite3.Connection
    scope: str
    captured_ms: int
    since_ms: int

    def __init__(self, scope: str, captured_ms: int, since_ms: int):
        object.__setattr__(self, "connection", sqlite3.connect(":memory:"))
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "captured_ms", captured_ms)
        object.__setattr__(self, "since_ms", since_ms)

    def close(self):
        self.connection.close()


@dataclass(frozen=True)
class QueueObservation:
    order_refused: bool | None = None
    order_expired: bool | None = None
    oldest_pending_exit_sec: float | None = None
    oldest_submitting_sec: float | None = None
    event_keys: tuple[tuple[str, str], ...] | None = None
    coverage: str = field(default="unknown", compare=False)


@dataclass(frozen=True)
class ResourceSample:
    captured_ms: int
    disk_blocks: int
    disk_free: int
    disk_available: int
    meminfo: bytes


def _fresh(captured_ms, now_ms):
    return (type(captured_ms) is int and type(now_ms) is int and captured_ms > 0
            and 0 <= now_ms - captured_ms <= MAX_SAMPLE_AGE_MS)


def _stamp(value):
    if type(value) is not str or not 0 < len(value) <= 40:
        raise ValueError("invalid_queue_timestamp")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    if parsed.tzinfo is None:
        raise ValueError("invalid_queue_timestamp")
    return parsed.timestamp() * 1000


def _rows(con, sql, parameters):
    budget = 1_048_576
    for index, row in enumerate(con.execute(sql, (*parameters, _ROW_CAP + 1))):
        if index >= _ROW_CAP:
            raise QueueEvidenceLimit("queue_observation_budget")
        if any(value is not None and type(value) is not str for value in row):
            raise ValueError("invalid_queue_observation_row")
        budget -= sum(len(value.encode("utf-8")) for value in row if value is not None)
        if budget < 0:
            raise QueueEvidenceLimit("queue_observation_budget")
        yield row


def _text(column, cap):
    # The fixed identifiers below are source constants, not SQL inputs.
    return (f"CASE WHEN {column} IS NULL OR (typeof({column})='text' "
            f"AND length(CAST({column} AS BLOB)) <= {cap}) THEN {column} ELSE x'00' END")


def observe_queue(sample: QueueSample | None, *, market: str, now_ms: int, track_events=False) -> QueueObservation:
    """Classify a bounded copy; never open a path, write or read a live DB."""
    if (type(sample) is not QueueSample or not _fresh(sample.captured_ms, now_ms)
            or type(sample.since_ms) is not int or not 0 <= sample.since_ms <= sample.captured_ms
            or type(market) is not str or market not in ("BTC/USD", "ETH/USD", "SOL/USD")):
        return QueueObservation()
    con = sample.connection
    if type(con) is not sqlite3.Connection or con.row_factory is not None or con.text_factory is not str:
        return QueueObservation()
    limited = False
    exhausted = False
    try:
        if con.execute("PRAGMA database_list").fetchall() != [(0, "main", "")]:
            return QueueObservation()
        if (con.execute("PRAGMA query_only").fetchone() != (1,)
                or con.execute("PRAGMA trusted_schema").fetchone() != (0,)
                or con.execute("PRAGMA temp_store").fetchone() != (2,)
                or con.in_transaction):
            return QueueObservation()
        ticks_left = 400

        def progress():
            nonlocal ticks_left, exhausted
            ticks_left -= 1
            exhausted = ticks_left <= 0
            return ticks_left <= 0

        con.set_progress_handler(progress, 1000)
        limited = True
        schema_rows = list(islice(con.execute("PRAGMA main.table_list"), 257))
        if len(schema_rows) > 256:
            return QueueObservation()
        tables = {name for schema, name, kind, *_ in schema_rows
                  if schema == "main" and kind == "table"}
        if not {"trade_intents", "paper_exit_events", "paper_buy_events"} <= tables:
            return QueueObservation()
        for table, condition in (
            ("paper_exit_events", "e.event='refused'"),
            ("paper_buy_events", "e.event='transition' AND e.status IN ('rejected','expired')"),
        ):
            if con.execute(f"""
                SELECT 1 FROM main.{table} e LEFT JOIN main.trade_intents q ON q.intent_id=e.intent_id
                WHERE q.intent_id IS NULL AND ({condition}) LIMIT 1
            """).fetchone():
                return QueueObservation()
        args = ("coinbase", market)
        refused, expired = False, False
        event_keys = set()
        terminal_rows = []
        journaled_terminal = set()
        exit_age, submitting_age = 0.0, 0.0

        def remember(code, origin, identity):
            if not track_events:
                return
            if type(identity) is not str or not identity or "\x00" in identity:
                raise ValueError("invalid_queue_event_identity")
            key = sha256(json.dumps([origin, identity], ensure_ascii=True).encode("ascii")).hexdigest()
            event_keys.add((code, key))

        def age(value):
            stamp = _stamp(value)
            if not 0 < stamp <= sample.captured_ms:
                raise ValueError("out_of_capture_queue_timestamp")
            return stamp, (sample.captured_ms - stamp) / 1000

        fields = ", ".join(_text(col, cap) for col, cap in (
            ("intent_id", 256), ("source", 40), ("side", 8), ("status", 16),
            ("created_ts", 40), ("updated_ts", 40), ("client_order_id", 320), ("meta", _META_CAP),
        ))
        for identity, source, side, status, created, updated, client_id, raw_meta in _rows(con, f"""
            SELECT {fields}
            FROM main.trade_intents
            WHERE venue=? AND symbol=? AND status IN ('queued','submitting','submitted','held','rejected','expired')
            LIMIT ?
        """, args):
            if status in ("rejected", "expired"):
                terminal_rows.append((identity, status, updated))
            if status == "submitting":
                submitting_age = max(submitting_age, age(updated)[1])
            if source == "strategy" and side == "sell" and status != "expired":
                if raw_meta is not None and (type(raw_meta) is not str or len(raw_meta) > _META_CAP):
                    raise ValueError("invalid_queue_meta")
                meta = _decode_payload(raw_meta) if raw_meta is not None else None
                if raw_meta is not None and meta is None:
                    raise ValueError("invalid_queue_meta")
                row = {"intent_id": identity, "side": side, "client_order_id": client_id, "meta": meta}
                if has_exit_marker(row):
                    exit_identity(row)
                    exit_age = max(exit_age, age(created)[1])

        # Exit refusals are repeatable; buy terminal transitions and their
        # current status row describe the same intent/terminal state.
        exit_id = "CASE WHEN typeof(e.event_id)='integer' AND e.event_id>0 THEN CAST(e.event_id AS TEXT) ELSE x'00' END"
        for stamp, identity in _rows(con, f"""
            SELECT {_text("e.ts", 40)}, {exit_id if track_events else 'NULL'}
            FROM main.paper_exit_events e JOIN main.trade_intents q ON q.intent_id=e.intent_id
            WHERE q.venue=? AND q.symbol=? AND q.source='strategy' AND q.side='sell' AND e.event='refused'
            LIMIT ?
        """, args):
            if age(stamp)[0] > sample.since_ms:
                refused = True
                remember("order_refused", "exit_event", identity)
        for stamp, status, identity in _rows(con, f"""
            SELECT {_text("e.ts", 40)}, {_text("e.status", 16)}, {_text('q.intent_id', 256) if track_events else 'NULL'}
            FROM main.paper_buy_events e JOIN main.trade_intents q ON q.intent_id=e.intent_id
            WHERE q.venue=? AND q.symbol=? AND q.side='buy' AND e.event='transition'
              AND e.status IN ('rejected','expired') LIMIT ?
        """, args):
            if track_events:
                journaled_terminal.add((identity, status))
            recent = age(stamp)[0] > sample.since_ms
            refused |= recent and status == "rejected"
            expired |= recent and status == "expired"
            if recent:
                remember("order_refused" if status == "rejected" else "order_expired", "terminal", identity)
        for identity, status, updated in terminal_rows:
            if (identity, status) in journaled_terminal:
                continue
            # Legacy and non-journaled terminal rows only provide a mutable
            # observation time, not proof of when the transition occurred.
            recent = age(updated)[0] > sample.since_ms
            refused |= recent and status == "rejected"
            expired |= recent and status == "expired"
            if recent:
                remember("order_refused" if status == "rejected" else "order_expired", "terminal", identity)
        return QueueObservation(refused, expired, exit_age, submitting_age,
                                tuple(sorted(event_keys)) if track_events else None, coverage="complete")
    except QueueEvidenceLimit:
        return QueueObservation(coverage="limit")
    except (sqlite3.Error, TypeError, ValueError, OverflowError, RecursionError):
        return QueueObservation(coverage="limit" if exhausted else "unknown")
    finally:
        if limited:
            con.set_progress_handler(None, 0)


def observe_resources(sample: ResourceSample | None, *, now_ms: int) -> HostObservation:
    if type(sample) is not ResourceSample or not _fresh(sample.captured_ms, now_ms):
        return HostObservation()
    total, free, available = sample.disk_blocks, sample.disk_free, sample.disk_available
    disk = None
    if (all(type(n) is int for n in (total, free, available))
            and 0 <= available <= free <= total <= 2**64 - 1 and total - free + available > 0):
        disk = 100 * (total - free) / (total - free + available)
    memory = None
    if type(sample.meminfo) is bytes and len(sample.meminfo) <= 16_384:
        values = {}
        for line in sample.meminfo.splitlines():
            key = line.split(b":", 1)[0]
            if key in (b"MemTotal", b"MemAvailable"):
                match = re.fullmatch(rb"(MemTotal|MemAvailable):[ \t]+([0-9]{1,19})[ \t]+kB", line)
                if not match or key in values:
                    values = {}
                    break
                values[key] = int(match[2])
        mem_total, mem_available = values.get(b"MemTotal", 0), values.get(b"MemAvailable")
        if mem_total > 0 and mem_available is not None and 0 <= mem_available <= mem_total:
            memory = 100 * (mem_total - mem_available) / mem_total
    return HostObservation(disk_pct=disk, memory_pct=memory)
