# Pass 2I — Resume Gate, Safe Mode, Safety Policy, Watchdog

**Date:** 2026-05-10
**Pass:** 2I
**Status:** COMPLETE

## Status update — 2026-05-11

- Historical finding `H5` remains valid as evidence of the resume/control-plane gap at audit time.
- Independently accepted remediations now exist on:
  - `codex/resume-gate-coherence` @ `62f50d643`
  - `codex/live-guard-failclosed` @ `4a1e10ec4`
- Those remediations have **not** been landed into the active soak checkout.
- Current blocker status is tracked in:
  - [audit_findings_status_2026_05_11.md](./audit_findings_status_2026_05_11.md)

---

## SHOWN findings

### Finding 1 — Drill 6 FAIL root cause confirmed in `resume_if_safe` (High)

`resume_if_safe()` calls `live_allowed(allow_kill_switch_armed=True, allow_system_guard_halted=True)`.

`live_allowed()` checks:
1. System guard (bypassed)
2. Kill switch (bypassed)
3. `is_live_enabled(cfg)` where cfg = load_user_yaml() -- NOT bypassed

`resume_if_safe()` never calls `set_live_enabled(cfg, True)`. If the config
does not have `live_enabled: True`, `is_live_enabled(cfg)` returns False,
`live_allowed()` returns `(False, 'risk_enable_live_false')`, and
`resume_if_safe()` exits with `{ok: False, resumed: False}`.
No arming signals are set.

**Drill 6 FAIL root cause confirmed:** The two arming flows are disconnected.
`resume_if_safe` sets arming signals but requires config; `live_enable_wizard`
sets config but doesn't call `resume_if_safe`. Each requires a precondition
the other doesn't set.

---

### Finding 2 — `resume_if_safe` has correct rollback on system_guard failure (Strength)

If `set_system_guard_state` fails after env var and arming file are set:

```python
os.environ.pop('CBP_EXECUTION_ARMED', None)
set_live_armed_state(False, ..., reason='rollback')
set_armed(True, ...)
```

Correct transactional rollback. Partial failure leaves system in known state.

---

### Finding 3 — `auto_disable_if_needed` is a startup safety check (Strength)

`auto_disable_live_on_start: True` by default. On startup, if live is enabled
OR kill switch disarmed OR system guard not halted, calls `disable_live_now()`.
Prevents starting in live-armed state after crash or unclean shutdown.

---

### Finding 4 — `DEFAULT_POLICY` uses zero for all limits (Noted)

```python
'max_daily_loss_usd': 0.0,
'max_trades_per_day': 0,
'max_notional_per_trade_usd': 0.0,
```

`validate_policy` accepts 0 as valid (checks `v < 0`). Zero is ambiguous --
'no limit' or 'disabled'? No production code confirmed to enforce
`safety_policy.read_policy()` limits.

---

### Finding 5 — `watchdog._pid_alive` cannot detect IDLE-on-crash (Noted)

`os.kill(pid, 0)` returns True if process exists regardless of activity.
A process in the `_safe_idle()` infinite sleep loop passes this check.
Confirms Section 3 IDLE-on-crash false-positive. Watchdog adds no observability
beyond the raw PID check.

---

## Summary

| Finding | Severity |
|---|---|
| `resume_if_safe` disconnected from config -- Drill 6 confirmed | **High** |
| `resume_if_safe` rollback on system_guard failure | **Strength** |
| `auto_disable_if_needed` startup safety check | **Strength** |
| DEFAULT_POLICY zeros ambiguous | Noted |
| watchdog cannot detect IDLE-on-crash | Noted |

---

## Updated High findings

| # | Finding | Severity |
|---|---|---|
| H4 | Governance enforcement dead code | High |
| H5 | `resume_if_safe` disconnected from config -- Drill 6 confirmed | **High** |
| H1 | VIEWER partial arming state | Medium |
| H2 | VIEWER writes API keys | Medium |
| H3 | VIEWER corrupts paper state | Medium |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2I
**Next:** `services/admin/` remaining or pivot to document H5 fix
