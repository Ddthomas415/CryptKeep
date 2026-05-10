# Execution, Routing, and Risk Gates Audit — Pass 1

**Date:** 2026-05-10
**Section:** 3. Execution, Routing, and Risk Gates
**Status:** COMPLETE

---

## Scope

- `services/execution/intent_executor.py`
- `scripts/run_intent_executor.py` + `run_intent_executor_safe.py`
- `scripts/run_live_reconciler_safe.py`
- `scripts/run_intent_consumer_safe.py`
- `services/execution/adapters/factory.py` (post-PR #37)
- `scripts/run_ops_risk_gate_service.py`

**Note:** `place_order.py`, `live_intent_consumer.py`, `live_reconciler.py`,
`fill_sink.py`, and `system_health.py` were audited earlier in this session.
Findings 1–11 are resolved on master via PRs #36–#40. This pass covers the
executor loop, safe wrappers, and mode-separation surfaces.

---

## Checklist status

- [x] Verified canonical submit owner by mode.
- [x] Verified safe-wrapper idle behavior on startup failure.
- [x] Verified paper/live mode separation in executor and adapter path.
- [x] Verified `_live_allowed()` gate in `intent_executor.py`.
- [x] Verified mode default in `run_intent_executor.py`.
- [~] Risk accounting write paths: covered by earlier audit (PRs #36, #39).

---

## SHOWN findings

### Finding 1 — Safe wrappers enter permanent IDLE on crash (Medium)

Both `run_intent_consumer_safe.py` and `run_live_reconciler_safe.py` use
`_safe_idle()` on both crash and nonzero `SystemExit`:

```python
except Exception as exc:
    log("reconciler crashed: " + repr(exc))
    log(traceback.format_exc())
    return _safe_idle()
```

`_safe_idle()` is an infinite `time.sleep(2.0)` loop. The process stays
alive so `bot_status.py` reports `running=True`, but the actual logic
has stopped.

**Impact:** A crashed executor or reconciler reports healthy. Intents
accumulate without processing. No automated alert that service is IDLE vs
active. The crash IS logged to the named log file — that is the only visible
signal.

---

### Finding 2 — Mode separation is explicit at arming and adapter boundary (Strength)

`intent_executor.py:35–45`:

```python
m = str(it["mode"]).lower()
if m == "live":
    ok, why = _live_allowed(cfg)   # calls is_live_enabled() canonical check
    if not ok:
        return {"ok": False, ...}
adapter = get_adapter(cfg=cfg, venue=v, mode=m)
```

`get_adapter(mode="paper")` → `PaperEngineAdapter` (no network, no credentials).
`get_adapter(mode="live")` → CCXT live exchange instance.

A paper intent cannot reach the live exchange. The separation is enforced at
both the arming check and the adapter factory.

---

### Finding 3 — Mode default is "paper" in executor (Strength)

`run_intent_executor.py:70`:

```python
mode = ex.get("mode", "paper")
```

Missing config defaults to paper, not live. Correct fail-safe.

---

### Finding 4 — Safe wrapper routes to wrong consumer for live use (Medium)

`run_intent_consumer_safe.py` delegates to `scripts.run_intent_consumer`.
`start_bot.py` starts intent_consumer as `run_live_intent_consumer.py run` directly.

These are different scripts. `run_live_intent_consumer` has the arming checks,
MQ gates, and orphan fixes from PR #39. `run_intent_consumer` is the paper-era
script. The safe wrapper wraps the wrong one for live use.

Currently not a live bug — `start_bot.py` uses the correct direct invocation.
But the safe wrapper is misleadingly named: if used instead of the direct
invocation, live guards would not be active.

---

## Summary

| Surface | Finding | Severity |
|---|---|---|
| Safe wrappers — IDLE on crash | PID reports running; logic stopped | Medium |
| Executor mode separation | Explicit at arming + adapter boundary | **Strong** |
| Mode default paper | Fail-safe default | **Strong** |
| Safe wrapper wrong consumer | Wraps paper-era script, not live script | Medium |

---

## UNVERIFIED points

- Whether any live deployment would use `run_intent_consumer_safe.py` instead
  of `run_live_intent_consumer.py` directly.
- Whether `check_system_health.py` can detect IDLE state (it probably cannot).
- Whether `run_intent_consumer` has received the same guards as
  `run_live_intent_consumer` post-PR #39.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Section 3 pass 1
**Next target:** Section 9 — Auth, Roles, and Safety Boundaries
