# Storage and State Integrity Audit — Pass 1

**Date:** 2026-05-10
**Section:** 4. Storage and State Integrity
**Status:** COMPLETE

---

## Scope

- `services/os/file_utils.py` — atomic write primitives
- `services/runtime/process_supervisor.py` — PID file writes
- `scripts/run_intent_executor.py`, `run_pipeline_loop.py` — status file writes
- `storage/paper_trading_sqlite.py` — paper order idempotency
- `storage/live_intent_queue_sqlite.py` — WAL mode + atomic risk claim
- `storage/strategy_state_store_sqlite.py` — strategy state upsert
- `storage/live_trading_sqlite.py` — fill idempotency

---

## Checklist status

- [x] Atomic write usage for runtime status files.
- [x] Queue transition invariants (covered in execution audit).
- [x] Fill journaling idempotency.
- [x] WAL mode on SQLite stores.
- [x] Paper order idempotency.
- [x] Strategy state upsert safety.
- [~] Crash-consistency in live_reconciler: covered earlier (PR #36).

---

## SHOWN findings

### Finding 1 — PID file write is not atomic (Low)

`services/runtime/process_supervisor.py:33`:
```python
_pidfile(name).write_text(str(int(pid)), encoding="utf-8")
```

Uses `Path.write_text()` — a direct non-atomic write. All other status file
writes in the codebase use `atomic_write()` from `services/os/file_utils.py`.

Impact: a partially-written PID file would cause `bot_status.py` to report
the service as not running. In practice PID files contain a 1–7 digit integer
so partial writes are extremely unlikely. Risk is theoretical but the
inconsistency is worth noting.

---

### Finding 2 — `atomic_write` is correctly implemented (Strength)

```python
def atomic_write(path, text, ...):
    fd, tmp = _sibling_temp_path(path)   # sibling temp in same dir
    ...
    os.replace(tmp, path)               # atomic on POSIX + Windows 3.3+
```

Sibling temp file + `os.replace()`. Failure cleans up temp before re-raising.
All runtime status files use it.

---

### Finding 3 — SQLite stores use WAL + NORMAL synchronous (Strength)

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

Confirmed on `live_intent_queue_sqlite`, `paper_trading_sqlite`.
WAL allows concurrent reads. `synchronous=NORMAL` flushes at checkpoints —
correct tradeoff for local desktop deployment.

---

### Finding 4 — Paper orders are idempotent on `client_order_id` (Strength)

```sql
client_order_id TEXT NOT NULL UNIQUE,  -- idempotency key
```

Insert uses `INSERT OR IGNORE`. Duplicate submission with same
`client_order_id` silently no-ops.

---

### Finding 5 — Live fills are idempotent on `fill_key` (Strength)

```python
"INSERT OR IGNORE INTO live_fills(fill_key, trade_id, ...) VALUES ..."
```

`fill_key` is `[venue, symbol, trade_id]`. Duplicate fill inserts silently
ignored. Reconciler retry safety from PR #36 relies on this.

---

### Finding 6 — Strategy state uses INSERT OR REPLACE (Noted)

```python
"INSERT OR REPLACE INTO strategy_state(...) VALUES ..."
```

Deletes and re-inserts on every upsert, changing `rowid`. No practical impact
given current schema (no FK relationships), but noted for future.

---

## Summary

| Surface | Atomic write | Idempotency | WAL |
|---|---|---|---|
| Runtime status files | ✅ atomic_write | N/A | N/A |
| PID files | ❌ write_text | N/A | N/A |
| live_intent_queue | WAL | BEGIN IMMEDIATE risk claim | ✅ |
| paper_trading | WAL | INSERT OR IGNORE on client_order_id | ✅ |
| live_trading fills | WAL | INSERT OR IGNORE on fill_key | ✅ |
| strategy_state | WAL | INSERT OR REPLACE | ✅ |

---

## UNVERIFIED points

- Whether all SQLite stores use WAL (spot-checked three, not exhaustive).
- Whether power-loss recovery gap from `synchronous=NORMAL` is documented.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Section 4
**Next target:** Section 5 — Market Data and Symbol Management
or Section 7 — AI Copilot and Alerting
