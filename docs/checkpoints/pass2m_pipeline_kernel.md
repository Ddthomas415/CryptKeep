# Pass 2M — Pipeline Router, Strategy Selector, ControlKernel

**Date:** 2026-05-10
**Pass:** 2M
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — `pipeline_router` default silent fallback to ema (Medium)

```python
strategy: str = "ema"   # default RouterCfg
# ...
return EMACrossoverPipeline(...)   # silent fallback for unknown
```

Same pattern as strategy_registry. Unknown strategy string silently runs EMA
cross. Active soak uses 'es_daily_trend' which routes correctly.

---

### Finding 2 — Kernel correctly blocks new risk for PAPER stage (Strength)

```python
new_risk = action == ACTION_ALLOW and stage not in (
    Stage.PAPER, Stage.SHADOW, Stage.SAFE_DEGRADED
)
```

Even ACTION_ALLOW returns `new_risk_allowed=False` in paper/shadow/safe_degraded.

---

### Finding 3 — `signal_from_ohlcv` bypasses ControlKernel entirely (Shown)

The supervised soak: `strategy_registry.compute_signal()` → `signal_from_ohlcv()`.
This path does NOT call `ControlKernel.evaluate()`. It does not check stage,
`new_risk_allowed`, or cognitive budget.

**Current soak:** No safety concern — paper adapter cannot place live orders.

**Future live deployment:** If supervised pipeline switches to `mode='live'`,
kernel stage gates (CAPPED_LIVE 1-contract cap, PAPER no-order, SAFE_DEGRADED
halt) would NOT apply. Live safety depends entirely on `_live_allowed()` in
`intent_executor.py` and the risk gate service.

---

### Finding 4 — 4-level fail-closed action hierarchy (Strength)

`_worst_action` takes the most severe action from all metric checks.
Any single metric at crit produces HALT regardless of others.
6 independent metrics: slippage, fill rate, recon drift, drawdown duration,
regime stability, alert count.

---

### Finding 5 — `dd_duration_days >= crit` auto-demotes to SAFE_DEGRADED (Shown)

```python
if dd_days >= t['dd_duration_days']['crit']:
    force_safe_degraded(self.strategy_id, reason=...)
```

Permanent stage demotion — operator must manually reset. Only fires from
`decide()` calls, not from the supervised pipeline's `signal_from_ohlcv()`
path (which bypasses the kernel).

---

### Finding 6 — `select_strategy` output not consumed by runner (Shown, known)

Runner picks strategy by config. `candidate_advisor` output is not consumed.
Previously confirmed production gap.

---

## Summary

| Finding | Severity |
|---|---|
| `pipeline_router` silent fallback to ema | Medium |
| Kernel blocks new risk for PAPER stage | **Strength** |
| `signal_from_ohlcv` bypasses kernel | Shown |
| 4-level fail-closed action hierarchy | **Strength** |
| `dd_duration_days` auto-demotes to SAFE_DEGRADED | Shown |
| `select_strategy` output not consumed | Shown (known) |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2M
**Next:** `services/control/cognitive_budget.py` or remediation planning
