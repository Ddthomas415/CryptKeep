# Pass 2T — Execution Layer Batch 3

**Date:** 2026-05-10
**Pass:** 2T
**Status:** COMPLETE for this batch

---

## SHOWN findings

### Finding 1 — risk_gates fails closed when limits unconfigured (Strength)

```python
cfg_limits = limits or LiveRiskLimits.from_trading_yaml()
if cfg_limits is None:
    logging.critical('RISK_GATE_FAIL_CLOSED: limits_unconfigured')
    return GateDecision(ok=False, reason='limits_unconfigured', ...)
```

If canonical_runtime.json absent and limits=None: logs CRITICAL, returns ok=False.
Correct fail-closed. Missing risk config blocks trading.

---

### Finding 2 — _executor_shared mtime-cached YAML is thread-safe (Strength)

Read outside lock. Cache invalidated on mtime change. Lock only held to
check/write cache entry. Correct pattern.

---

### Finding 3 — live_fill_mapper.map_order_to_fills is a skeleton stub (Medium)

```python
# Phase IN/IO: Live Fill Mapper (skeleton)
def map_order_to_fills(order):
    return []
```

Always returns empty list. Same pattern as exit_rules.evaluate_exit.
Actual fill mapping goes through CanonicalFillSink (REVIEWED Pass 2A).
Callers relying on this would receive no fills.

---

### Finding 4 — safety.SafetyGates zero defaults = no enforcement (Medium)

All three limits default to 0. Truthiness checks: 0 = skip gate.

Three parallel safety gate paths with different fail behaviors:

| Path | Source | Zero/missing config behavior |
|---|---|---|
| safety.py | safety: in user.yaml | Skips all gates |
| risk_gates.py | canonical_runtime.json | Fails closed (ok=False) |
| live_risk_gates.py | risk.live: in user.yaml | Returns None |

Which path live submission actually calls determines enforcement.

---

### Finding 5 — funnel.FunnelExecutor explicitly labeled incomplete (Noted)

Docstring: 'Minimal routing shim only. Not the full gate-enforcement funnel.'

---

### Finding 6 — _EXECUTION_SAFETY_CIRCUIT circuit breaker (Strength)

_PreflightCircuitState tracks consecutive failures. Circuit opens to prevent
rapid retry storms on sustained infrastructure failures.

---

## Summary

| Finding | Severity |
|---|---|
| risk_gates fails closed when unconfigured | **Strength** |
| _executor_shared mtime YAML cache thread-safe | **Strength** |
| live_fill_mapper.map_order_to_fills stub | Medium |
| safety.SafetyGates zero defaults no enforcement | Medium |
| Three parallel safety gate paths different behaviors | Shown |
| funnel explicitly incomplete | Noted |
| Circuit breaker on preflight failures | **Strength** |

---

## Remaining NOT_AUDITED ~51 files in services/execution/

Critical: ccxt_fills.py, exchange_client.py, intent_reconciler.py,
live_event_executor.py, live_trader_loop.py, normalize_ccxt.py,
order_reconciliation.py, paper_engine.py, reconciliation.py,
retry_policy.py, strategy_runner.py, venue_capabilities.py

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2T
**Key open question:** Which of the 3 safety gate paths does live submission
actually invoke? Trace needed.
