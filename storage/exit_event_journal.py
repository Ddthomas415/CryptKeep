"""Ordered provisional exit events; not a ledger of exchange fills.

An event is prepared before enqueue. Queue confirmation belongs to the caller.
An unresolved first event prevents later events from overtaking it.

Each event row is in one of these conditions:

  pending                 prepared; whether its intent reached the queue is
                          not recorded here yet.
  pending + confirmed     the intent is known to be in the queue. This can be
                          recorded for any event, whatever its place in line;
                          APPLYING it still waits for every earlier event.
                          It survives the death of the process. The file is
                          opened WAL with synchronous=NORMAL, so a power or
                          operating-system failure can lose the last commits.
  pending + quarantined   evidence that cannot be used (unreadable payload, a
                          value that is not a finite number). The raw text is
                          kept. It is never applied and never discarded here,
                          and events behind it do not overtake it.
  applied                 counted, once, in the same transaction as the
                          counters it changed. Permanent.
  unwritten               the intent never reached the queue. Permanent. A
                          confirmed or quarantined event cannot become this.

For whoever wires this in:
  - ``prepare`` returns normally when the same intent id and payload already
    exist, WHATEVER the row's status (applied, unwritten, quarantined). An
    attempt to enqueue again after "unwritten" must therefore use a new intent
    id, or its sell will never be counted.
  - A quarantined event blocks its scope until someone resolves it outside
    this module; there is no release method here.
  - The first open of a table created by the first version needs a write
    lock, even for a read.
  - ``apply`` (the production call) refuses an event that is not confirmed.
    ``settle(written=True)`` keeps the first version's meaning: the caller's
    True is itself the confirmation.
  - Evidence that an event marked unwritten was written after all is a
    contradiction: ``confirm`` and ``apply`` raise instead of answering False.
  - A pending row whose scope text is damaged belongs to no scope that can
    be named. While one exists, ``has_unresolved`` answers True for EVERY
    scope and nothing is applied anywhere; it is cleared outside this module.
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
from collections.abc import Callable, Collection

from storage import strategy_state_sqlite as state_store


class ExitEventJournal:
    def _connect(self):
        con = state_store._connect()
        con.execute('''CREATE TABLE IF NOT EXISTS exit_events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            intent_id TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','applied','unwritten'))
        )''')
        try:
            _upgrade_schema(con)
        except BaseException:
            con.close()
            raise
        return con

    def prepare(self, scope: str, intent_id: str, payload: dict) -> None:
        if not scope or not intent_id or not isinstance(payload, dict):
            raise ValueError('invalid_exit_event')
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
        con = self._connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            old = con.execute('SELECT scope,payload FROM exit_events WHERE intent_id=?', (intent_id,)).fetchone()
            if old is not None:
                if old != (scope, encoded):
                    raise ValueError('exit_event_identity_conflict')
            else:
                con.execute('INSERT INTO exit_events(scope,intent_id,payload,status) VALUES(?,?,?,?)',
                            (scope, intent_id, encoded, 'pending'))
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def pending(self, scope: str) -> list[tuple[str, dict]]:
        """Pending events as (intent id, payload), oldest first.

        Kept as first written: it includes quarantined events and raises if a
        stored payload cannot be parsed. Callers that must not stop on bad
        evidence use ``unresolved`` instead.
        """
        con = self._connect()
        try:
            rows = con.execute("SELECT intent_id,payload FROM exit_events WHERE scope=? AND status='pending' ORDER BY seq", (scope,)).fetchall()
            return [(identity, json.loads(payload)) for identity, payload in rows]
        finally:
            con.close()

    def settle(self, scope: str, intent_id: str, *, written: bool,
               reduce: Callable[[dict, Callable[[str], str | None]], dict[str, str]],
               allowed_keys: Collection[str] | None = None,
               _require_confirmed: bool = False) -> bool:
        """Atomically reduce a confirmed event and mark it, or mark it unwritten.

        The reducer must only calculate performance-counter updates, not issue
        orders or clear stop state. It reads current counters inside this same
        write transaction. Queue uncertainty must never be passed as False.

        ``allowed_keys``: when given (the production mode; see ``apply``),
        the reducer may return only these keys, and every value must be an
        int, a finite float, or a string that reads as a finite number.
        Anything else is refused and nothing is written.
        Without it (as the first version of this module was written, and as
        its tests call it) keys are not restricted and a string value is
        stored as given; values of any other kind than str, int or finite
        float are still refused. Subclasses of str, int and float are never
        accepted. This guards against mistakes, not against a reducer that
        goes out of its way to reach the database.

        Refused, with nothing changed: a quarantined event (either way); an
        event whose payload cannot be read (either way); marking a confirmed
        event unwritten.
        """
        if type(written) is not bool:
            raise ValueError('exit_confirmation_required')
        if allowed_keys is not None:
            if isinstance(allowed_keys, (str, bytes)):
                raise ValueError('exit_reducer_allowed_keys_invalid')
            allowed_keys = frozenset(allowed_keys)
            if not allowed_keys or not all(type(key) is str and key for key in allowed_keys):
                raise ValueError('exit_reducer_allowed_keys_invalid')
        con = self._connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute(
                'SELECT scope,CAST(payload AS BLOB),status,confirmed,quarantined FROM exit_events WHERE intent_id=?',
                (intent_id,),
            ).fetchone()
            if row is None or row[0] != scope:
                raise ValueError('unknown_exit_event')
            if row[2] != 'pending':
                if written and row[2] == 'unwritten':
                    raise ValueError('exit_event_marked_unwritten')
                con.commit()
                return False
            if row[4]:
                raise ValueError('exit_event_quarantined')
            if _damaged_scope_pending(con):
                raise ValueError('exit_event_scope_damaged')
            if written and _require_confirmed and not row[3]:
                raise ValueError('exit_event_unconfirmed')
            if not written and row[3]:
                raise ValueError('exit_event_confirmed_written')
            event = _decode_payload(row[1])
            if event is None:
                # Not usable either way: it is not this method's place to
                # decide that evidence it cannot read was never written.
                raise ValueError('exit_event_unreadable')
            first = con.execute("SELECT intent_id FROM exit_events WHERE scope=? AND status='pending' ORDER BY seq LIMIT 1", (scope,)).fetchone()
            if first[0] != intent_id:
                raise ValueError('earlier_exit_unresolved')

            def get(key):
                value = con.execute('SELECT v FROM strategy_state WHERE k=?', (key,)).fetchone()
                return value[0] if value else None

            if written:
                updates = _checked_updates(reduce(event, get), allowed_keys)
                for key, value in updates.items():
                    con.execute('INSERT OR REPLACE INTO strategy_state(k,v,updated_ts) VALUES(?,?,?)',
                                (key, value, state_store._now()))
            con.execute('UPDATE exit_events SET status=? WHERE intent_id=?',
                        ('applied' if written else 'unwritten', intent_id))
            con.commit()
            return True
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def confirm(self, scope: str, intent_id: str) -> bool:
        """Record that this event's intent is in the queue. Order does not matter.

        This is evidence only: nothing is counted. The event is applied later,
        in its turn, by ``settle(..., written=True)``, and from then on that
        needs no further look at the queue. True if the event is pending (now
        confirmed, or already was); False if it is already applied. An event
        already marked unwritten raises: the two records contradict each other.
        """
        con = self._connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT scope,status FROM exit_events WHERE intent_id=?', (intent_id,)).fetchone()
            if row is None or row[0] != scope:
                raise ValueError('unknown_exit_event')
            if row[1] == 'unwritten':
                raise ValueError('exit_event_marked_unwritten')
            if row[1] != 'pending':
                con.commit()
                return False
            con.execute('UPDATE exit_events SET confirmed=1 WHERE intent_id=?', (intent_id,))
            con.commit()
            return True
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def quarantine(self, scope: str, intent_id: str, reason: str) -> bool:
        """Set a pending event aside. Its stored payload is not touched.

        True if the event is pending (now quarantined, or already was); False
        if it is already applied or unwritten. There is deliberately no method
        here to release a quarantined event.
        """
        con = self._connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT scope,status,quarantined FROM exit_events WHERE intent_id=?', (intent_id,)).fetchone()
            if row is None or row[0] != scope:
                raise ValueError('unknown_exit_event')
            if row[1] != 'pending':
                con.commit()
                return False
            if not row[2]:
                con.execute('UPDATE exit_events SET quarantined=1, note=? WHERE intent_id=?', (str(reason), intent_id))
            con.commit()
            return True
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def quarantine_raw(self, scope: str, intent_id: str, raw: str, reason: str, *, confirmed: bool = False) -> None:
        """Keep evidence that ``prepare`` would refuse, exactly as given.

        For an event whose value is not usable (for example a PnL that is not
        a finite number) or for stored text that cannot be parsed. It takes
        its place in line like any other event, is never applied, and events
        behind it wait. ``confirmed=True`` records that the intent is known to
        be in the queue; the event need not have been prepared first.

        Calling it again with the same text for the same scope keeps the row
        and its first reason; a later ``confirmed=True`` is recorded, a later
        ``confirmed=False`` does not withdraw one. The same intent id with
        different text or scope, or one that already exists as an ordinary
        (not quarantined) event, is refused.
        """
        if not scope or not intent_id or type(raw) is not str or type(confirmed) is not bool:
            raise ValueError('invalid_exit_event')
        con = self._connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            old = con.execute(
                'SELECT scope,CAST(payload AS BLOB),quarantined FROM exit_events WHERE intent_id=?', (intent_id,),
            ).fetchone()
            if old is not None:
                if (old[0], bytes(old[1] or b''), old[2]) != (scope, raw.encode('utf-8'), 1):
                    raise ValueError('exit_event_identity_conflict')
                if confirmed:
                    con.execute("UPDATE exit_events SET confirmed=1 WHERE intent_id=? AND status='pending'", (intent_id,))
            else:
                con.execute(
                    'INSERT INTO exit_events(scope,intent_id,payload,status,confirmed,quarantined,note) '
                    'VALUES(?,?,?,?,?,?,?)',
                    (scope, intent_id, raw, 'pending', 1 if confirmed else 0, 1, str(reason)),
                )
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def unresolved(self, scope: str) -> list[dict]:
        """Every pending event of the scope, oldest first. A bad payload never makes it raise.

        Each entry: intent_id, seq, confirmed, quarantined, note, raw, payload
        and damaged. ``raw`` is the stored text, or the stored bytes when they
        are not valid UTF-8. ``payload`` is the decoded dict, or None when the
        stored value is not a JSON object that ``prepare`` could have written
        (finite numbers only, no repeated keys). ``damaged`` is True when the
        stored intent id is not valid text: the row then cannot be addressed
        by any method here (its ``intent_id`` is shown with the bad bytes
        replaced) and it blocks its scope until it is dealt with by hand.
        """
        _check_scope(scope)
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT seq,CAST(intent_id AS BLOB),CAST(payload AS BLOB),confirmed,quarantined,CAST(note AS BLOB) "
                "FROM exit_events WHERE scope=? AND status='pending' ORDER BY seq", (scope,),
            ).fetchall()
        finally:
            con.close()
        out = []
        for seq, identity, blob, confirmed, quarantined, note in rows:
            blob = bytes(blob or b'')
            try:
                raw = blob.decode('utf-8')
            except UnicodeDecodeError:
                raw = blob
            identity = bytes(identity or b'')
            try:
                identity_text, damaged = identity.decode('utf-8'), False
            except UnicodeDecodeError:
                identity_text, damaged = identity.decode('utf-8', 'replace'), True
            out.append({
                'seq': seq, 'intent_id': identity_text, 'raw': raw, 'payload': _decode_payload(blob),
                'confirmed': bool(confirmed), 'quarantined': bool(quarantined),
                'note': None if note is None else bytes(note).decode('utf-8', 'replace'),
                'damaged': damaged,
            })
        return out

    def has_unresolved(self, scope: str) -> bool:
        """True while anything in the scope is neither applied nor unwritten.

        Also True, for every scope, while any pending row's scope text is
        damaged: that row may be this scope's and cannot be told apart.
        """
        _check_scope(scope)
        con = self._connect()
        try:
            if con.execute(
                "SELECT 1 FROM exit_events WHERE scope=? AND status='pending' LIMIT 1", (scope,),
            ).fetchone() is not None:
                return True
            return _damaged_scope_pending(con)
        finally:
            con.close()


    def status_of(self, intent_id: str) -> dict | None:
        """Scope, status, confirmed and quarantined of one event, or None if it was never recorded."""
        con = self._connect()
        try:
            row = con.execute(
                'SELECT scope,status,confirmed,quarantined,seq FROM exit_events WHERE intent_id=?', (intent_id,),
            ).fetchone()
        finally:
            con.close()
        if row is None:
            return None
        return {'scope': row[0], 'status': row[1], 'confirmed': bool(row[2]), 'quarantined': bool(row[3]), 'seq': row[4]}

    def last(self, scope: str) -> dict | None:
        """The most recently recorded event of the scope, whatever its status, or None."""
        con = self._connect()
        try:
            row = con.execute(
                'SELECT intent_id,CAST(payload AS BLOB),status,seq FROM exit_events WHERE scope=? ORDER BY seq DESC LIMIT 1',
                (scope,),
            ).fetchone()
        finally:
            con.close()
        if row is None:
            return None
        return {'intent_id': row[0], 'payload': _decode_payload(row[1]), 'status': row[2], 'seq': row[3]}

    def apply(self, scope: str, intent_id: str, *, reduce, allowed_keys: Collection[str]) -> bool:
        """Apply a CONFIRMED event, with the key list required. For production callers.

        An event that was never confirmed is refused (``exit_event_unconfirmed``).
        """
        if allowed_keys is None:
            raise ValueError('exit_reducer_allowed_keys_invalid')
        return self.settle(scope, intent_id, written=True, reduce=reduce, allowed_keys=allowed_keys,
                           _require_confirmed=True)


def _check_scope(scope) -> None:
    if type(scope) is not str or not scope:
        raise ValueError('invalid_exit_scope')


def _damaged_scope_pending(con) -> bool:
    """True if any pending row's scope is not valid text."""
    for (blob,) in con.execute("SELECT DISTINCT CAST(scope AS BLOB) FROM exit_events WHERE status='pending'"):
        try:
            bytes(blob or b'').decode('utf-8')
        except UnicodeDecodeError:
            return True
    return False


_PLAIN_NUMBER = re.compile(r'-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?')

_ADDED_COLUMNS = (
    ('confirmed', 'INTEGER NOT NULL DEFAULT 0'),
    ('quarantined', 'INTEGER NOT NULL DEFAULT 0'),
    ('note', 'TEXT'),
)
_INDEX = 'exit_events_scope_status_seq'


def _schema_current(con) -> bool:
    have = {row[1] for row in con.execute('PRAGMA table_info(exit_events)').fetchall()}
    if not all(name in have for name, _ in _ADDED_COLUMNS):
        return False
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (_INDEX,)).fetchone() is not None


def _upgrade_schema(con) -> None:
    """Bring a table created by the first version of this module up to date in place.

    Old rows keep their meaning (not confirmed, not quarantined). Nothing is
    written, and no write lock is taken, once the table is current. The
    upgrade itself runs under a write lock and checks again inside it, so two
    processes opening an old table at the same moment do not collide.
    """
    if _schema_current(con):
        return
    con.execute('BEGIN IMMEDIATE')
    try:
        have = {row[1] for row in con.execute('PRAGMA table_info(exit_events)').fetchall()}
        for name, ddl in _ADDED_COLUMNS:
            if name not in have:
                con.execute(f'ALTER TABLE exit_events ADD COLUMN {name} {ddl}')
        con.execute(f'CREATE INDEX IF NOT EXISTS {_INDEX} ON exit_events(scope, status, seq)')
        con.commit()
    except BaseException:
        con.rollback()
        raise


def _checked_updates(result, allowed_keys) -> dict[str, str]:
    """The reducer's result as {key: text to store}, or ValueError. Nothing is written here."""
    out: dict[str, str] = {}
    for key, value in dict(result).items():
        if type(key) is not str or not key:
            raise ValueError('exit_reducer_key_invalid')
        if allowed_keys is not None and key not in allowed_keys:
            raise ValueError(f'exit_reducer_key_not_allowed:{key}')
        if type(value) is int:
            try:
                finite = math.isfinite(float(value))
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError(f'exit_reducer_value_invalid:{key}')
            text = str(value)
        elif type(value) is float:
            if not math.isfinite(value):
                raise ValueError(f'exit_reducer_value_invalid:{key}')
            text = repr(value)
        elif type(value) is str:
            if allowed_keys is not None:
                if _PLAIN_NUMBER.fullmatch(value) is None:
                    raise ValueError(f'exit_reducer_value_invalid:{key}')
                try:
                    number = float(value)
                except ValueError:
                    raise ValueError(f'exit_reducer_value_invalid:{key}') from None
                if not math.isfinite(number):
                    raise ValueError(f'exit_reducer_value_invalid:{key}')
            text = value
        else:
            raise ValueError(f'exit_reducer_value_invalid:{key}')
        out[key] = text
    return out


def _reject_repeated_keys(pairs):
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError('repeated_key')
    return dict(pairs)


def _decode_payload(raw) -> dict | None:
    """The stored payload as a dict, or None.

    Readable means: valid UTF-8 text holding a JSON object that ``prepare``
    could have written, so no NaN or infinity however spelled (including a
    number too large for a float) and no repeated key.
    """
    try:
        if isinstance(raw, (bytes, memoryview)):
            raw = bytes(raw).decode('utf-8')
        value = json.loads(raw, object_pairs_hook=_reject_repeated_keys)
        if not isinstance(value, dict):
            return None
        json.dumps(value, allow_nan=False)
    except Exception:
        return None
    return value
