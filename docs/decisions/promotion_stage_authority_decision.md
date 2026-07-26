# Promotion Stage Authority Decision

**Status:** RESOLVED - gate-enforced operator entrypoint, 2026-07-12.

## Decision

The documented operator promotion path must consume the promotion-gate verdict
before it mutates deployment stage. A promotion command that cannot verify a
ready gate fails closed.

## Implemented Boundary

`scripts/show_control_kernel_status.py --promote` checks
`scripts/check_promotion_gates.py::run_check()` for the strategy's current stage
before calling `deployment_stage.promote()`.

Current machine gate support is scoped to `es_daily_trend_v1`. Promotion of any
other strategy through this entrypoint is blocked until that strategy has an
explicit gate implementation or authorization model.

## Rationale

`deployment_stage.promote()` changes allocation authority. The documented
Makefile/README path previously reached that mutation without consuming the
gate verdict. The gate itself was fail-closed, but the stage transition did not
depend on it.

This decision closes the documented operator path while preserving the low-level
stage-machine API for unit tests and internal state-machine use.

## Executable Guard

`tests/test_promotion_stage_authority_decision_guard.py` pins the
gate-enforced operator entrypoint, implemented boundary, strategy scope
boundary, authority rationale, and backlog link so promotion-stage authority
cannot silently drift back to a gate-bypassing operator path.
