# Pass 2N — Cognitive Budget and Deployment Stage

**Date:** 2026-05-10
**Pass:** 2N
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — cognitive_budget uses atomic_write correctly (Strength)

```python
def _save(data):
    atomic_write(_budget_path(), json.dumps(data, indent=2))
```

One of the few advisory state files that correctly uses atomic_write.

---

### Finding 2 — Alert dedup prevents double-counting per type (Strength)

```python
if not any(a.get('type') == alert_type for a in alerts):
    alerts.append({...})
```

Same alert type counted once regardless of how many times it fires. Correct.

---

### Finding 3 — Off-by-one between kernel threshold and budget breach (Noted)

Kernel: `'alert_count': {'crit': 4}` -- halts at >= 4 alerts.
Budget: `breach = len(alerts) > 4` -- breaches at 5+ alerts.

At exactly 4 alerts: kernel HALT, but `check_budget()['breach'] = False`.
Not a safety issue (kernel is the enforcer), but the counts diverge at 4.

---

### Finding 4 — force_safe_degraded bypasses can_transition (Confirmed H4)

`force_safe_degraded` -> `demote()` writes directly to stage store.
Does not call `can_transition` from campaign_state_machine.

Third independent confirmation of H4: no production path consults the
governance state machine.

---

### Finding 5 — action_allowed not called from supervised pipeline (Shown)

`action_allowed` is a correct gate but only reached from `decide()`
(standalone paper campaign runner). The supervised pipeline's
`signal_from_ohlcv` does not call it.

---

### Finding 6 — check_budget reads file on every call (Noted)

`_load()` opens and reads cognitive_budget.json every invocation.
`ControlKernel.evaluate()` calls it every decision. At poll_sec=10,
6 reads/min per strategy. Low overhead locally, but uncached.

---

## H4 final status

Three independent paths confirmed to bypass governance state machine:
1. `force_safe_degraded` -> `demote()` -- no can_transition
2. `ControlKernel.evaluate()` -- no can_transition
3. `signal_from_ohlcv` -- no can_transition, no action_allowed

---

## Summary

| Finding | Severity |
|---|---|
| cognitive_budget atomic_write | **Strength** |
| Alert dedup per type | **Strength** |
| Off-by-one at alert_count=4 | Noted |
| force_safe_degraded bypasses can_transition | Confirmed H4 |
| action_allowed not called from supervised pipeline | Shown |
| check_budget file read on every call | Noted |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2N
**Next:** `services/control/allocator.py`, `runtime_identity.py`, or remediation planning
