# Pass 2G — Admin Arming Wizards and H1 Depth

**Date:** 2026-05-10
**Pass:** 2G — admin arming surfaces; H1 re-evaluated
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — `system_guard` uses proper atomic writes (Strength)

Implements its own `_write_atomic`: sibling temp + `os.replace`. Correct pattern.
System guard state file is always written atomically.

---

### Finding 2 — `get_state(fail_closed=False)` defaults to RUNNING (Noted)

Missing system guard file + `fail_closed=False` = RUNNING (trading allowed).
`live_guard.live_allowed()` uses `fail_closed=False`. Softer than kill switch
(which defaults to ARMED/blocked). Partially mitigated by kill switch and
`is_live_enabled()` gating independently.

---

### Finding 3 — `live_enable_wizard` is the correct 5-step arming sequence (Strength)

```
1. set_live_enabled(cfg, True) -- config
2. os.environ[CBP_EXECUTION_ARMED] = YES -- env var
3. set_live_armed_state(True) -- runtime file
4. live_enabled_and_armed() -- verify both
5. set_system_guard_state(RUNNING) -- only if armed
   _log_audit(ENABLE_LIVE) -- audit log
```

System guard is only RUNNING after both conditions verified. Correct.

---

### Finding 4 — H1 re-evaluated: VIEWER partial arm only (Important Clarification)

`update_automation_view` calls only `set_live_enabled(cfg, True)` -- step 1 of 5.
It does NOT set the env var, arming file, or system guard. It does NOT call
`live_enabled_and_armed()` to verify. No audit log is written.

`place_order` calls `live_enabled_and_armed()` which checks BOTH config AND
arming signal. A VIEWER can set config to live but cannot satisfy the arming
signal condition.

**H1 severity: Medium (not High).** VIEWER cannot trigger live orders.
But VIEWER can create config state inconsistency and no audit trail is written.
Fix still required.

---

### Finding 5 — `live_disable_wizard` correctly severs all arming conditions (Strength)

Disarms: config, runtime arming file, system guard HALTED, kill switch, audit log.
Symmetric with enable_wizard. Complete teardown.

---

## Summary

| Finding | Severity |
|---|---|
| `system_guard` atomic writes | **Strength** |
| `get_state(fail_closed=False)` defaults RUNNING | Noted |
| `live_enable_wizard` correct 5-step | **Strength** |
| H1 re-evaluated: partial arm only; full arm blocked | Medium (clarified) |
| `live_disable_wizard` complete teardown | **Strength** |

---

## H1 severity update

**Previous:** High -- VIEWER can arm live
**Updated:** Medium -- VIEWER creates partial config inconsistency; full arming
blocked by `live_enabled_and_armed()` two-condition check. Fix still required.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2G
**Next:** `services/admin/config_editor.py`, `preflight.py`,
or `services/profiles/bundles.py`
