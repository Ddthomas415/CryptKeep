# Pass 2J — Service Controls, Repair, Reconcile, State Report

**Date:** 2026-05-10
**Pass:** 2J
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — `stop_service_from_pidfile` validates name before acting (Strength)

Two guards before any PID file access:
1. Regex whitelist `^[a-zA-Z0-9_-]+$` -- no path traversal
2. Known service list check -- can only stop registered services

Returns `{ok: False, error: 'unknown_service_name'}` for unregistered names.

---

### Finding 2 — `state_report._redact` protects credentials (Strength)

Recursive redaction over nested dicts and lists. Catches: `apikey`, `api_key`,
`secret`, `api_secret`, `passphrase`, `password`, `token`, `private_key`.
Case-insensitive key matching. Replaces with `***REDACTED***`.

---

### Finding 3 — `execute_reset` requires typed confirmation (Strength)

```python
CONFIRM_TEXT = 'RESET STATE'
if typed != CONFIRM_TEXT:
    return {'ok': False, 'reason': 'confirmation_mismatch'}
```

Destructive state reset requires exact text match. Static string (not
session-specific) -- sufficient for single-user local deployment.

---

### Finding 4 — `reconcile_safe_steps` is correctly read-only (Strength)

Labeled 'Non-destructive reconciliation helper'. `require_exchange_ok=False`
default -- runs even when exchange is unreachable. Read-only snapshot
comparisons only.

---

### Finding 5 — REDACT_KEYS misses CBP_-prefixed env var names (Noted)

`CBP_API_KEY`, `CBP_API_SECRET`, `CBP_PASSPHRASE` use `CBP_` prefix.
If any state snapshot includes raw env var dicts, these would not be redacted.
Not confirmed whether env vars appear in snapshots.

---

## Summary

| Finding | Severity |
|---|---|
| `stop_service_from_pidfile` validates name | **Strength** |
| `_redact` protects credentials | **Strength** |
| `execute_reset` typed confirmation | **Strength** |
| `reconcile_safe_steps` read-only | **Strength** |
| REDACT_KEYS misses CBP_ prefix | Noted |

---

## `services/admin/` coverage: 16 of 25 files reviewed

Not yet read: `build_runner.py`, `connectivity.py`, `first_run_wizard.py`,
`journal_exchange_reconcile.py`, `master_read_only.py`, `position_reconcile.py`,
`system_diagnostics.py`, `wizard_state.py`.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2J
**Next:** `services/strategies/` full reads, or remediation planning for H4/H5
