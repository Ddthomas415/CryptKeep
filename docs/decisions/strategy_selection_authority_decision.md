# Strategy Selection Authority Decision

**Status:** RESOLVED - Option A adopted on 2026-07-12 after independent review.

## Decision

The configured strategy identity is the only execution authority in the strategy
runner. `strategy_selector` and advisor output are advisory only; their output
must not become the executed strategy through a fallback chain.

## Boundary

The enforcement boundary is the `strategy_runner` resolution point:

```python
selected_strategy = str(cfg.get("strategy_id") or "")
```

A missing strategy name still resolves to the accepted `ema_cross` default inside
`_cfg()`. An explicitly empty or unsupported identity remains empty/unsupported
and must flow to the registry fail-closed path: `ok=false`, `unknown_strategy`,
`hold`.

## Rationale

A fallback is an authority transition. The prior public-OHLCV path allowed
`selection.get("selected_strategy")` or a silent `"ema_cross"` default to replace
an explicitly invalid configured identity before the registry could reject it.
That bypassed the intended fail-closed behavior for unknown strategy names.

The synthetic-tick path did not use `selected_strategy` as execution authority;
it executes from the validated strategy block. Its fallback still created an
evidence-integrity risk by labelling an invalid identity as `ema_cross`, so the
same no-substitution rule applies there as well.

## Invariants

- Advisory selector output may be recorded as context but may not execute.
- Explicitly invalid strategy identity fails closed; it is not substituted.
- Missing strategy name continues to use the existing `ema_cross` default.
- Synthetic execution continues to use the strategy block, not the reporting
  label.

## Executable Guard

`tests/test_strategy_selection_authority_decision_guard.py` pins configured
strategy identity as the only execution authority, advisory selector boundaries,
synthetic evidence-label boundaries, invariants, and backlog linkage so
selection/advisor output cannot silently regain execution authority.
