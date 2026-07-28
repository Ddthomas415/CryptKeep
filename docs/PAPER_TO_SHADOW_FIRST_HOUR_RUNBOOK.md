# Paper To Shadow First-Hour Runbook

Date: 2026-07-03
Status: written, not rehearsed

## Purpose

This runbook defines the first hour after a paper strategy is approved for
shadow review. It is an operator checklist, not an automatic promotion script.

## Preconditions

Do not start this runbook unless all are true:

- paper machine gate is clear from fresh operator-host output
- manual strategy review is written and accepted
- backtest/expectancy baseline is populated or explicitly waived
- shadow would-be-fill recorder is implemented and accepted
- deployment stage remains non-live until explicitly changed
- live routing remains disabled
- kill switch status is known and reachable

## Ground-Truth Commands

Run from the canonical operator host:

```bash
make status-paper-gate-qualification
```

Then inspect shadow readiness without changing stage:

```bash
./.venv/bin/python scripts/check_promotion_gates.py --stage shadow --json
```

Expected before promotion:

- `current_stage` is still `paper`
- `evidence_scope.status` is `not_started`
- shadow gates are not passed by paper evidence

## First-Hour Checklist

1. Save the fresh gate output into a dated checkpoint.
2. Confirm the strategy decision record says `advance_to_shadow_review`.
3. Confirm no retirement triggers are active.
4. Confirm `observe_only` is enabled for the shadow path.
5. Confirm the would-be-fill recorder writes shadow evidence without venue
   orders.
6. Promote the stage only through the accepted stage-control path.
7. Start the shadow session.
8. Verify signal evidence is stamped `_stage=shadow`.
9. Verify would-be-fill evidence includes intended side, quantity, reference
   price, bid/ask or depth, estimated fill, slippage, strategy id, and
   provenance.
10. Verify live intent/order tables remain unchanged.
11. Verify no venue orders exist from the shadow session.
12. Run the shadow gate query again and save output.
13. Watch one full signal/evidence cycle.
14. Record any blocked signal, missing spread/depth, or recorder failure.

## Abort Conditions

Abort and revert to paper observation if any condition is true:

- stage output does not match the intended transition
- live routing is enabled unexpectedly
- any venue order is created
- shadow evidence is missing `_stage=shadow`
- would-be-fill evidence is not written
- spread/depth is absent when required
- operator cannot verify kill-switch status

## Rollback

Rollback must be documented. Minimum steps:

1. Stop the shadow session.
2. Set stage back to the prior accepted state using the accepted control path.
3. Confirm no venue orders exist.
4. Save gate/status output after rollback.
5. Write a checkpoint explaining why the runbook aborted.

## Proof Still Required

This document does not prove the first hour has been rehearsed. A future
checkpoint must show:

- command outputs
- stage before/after
- shadow evidence path
- zero venue orders
- rollback evidence or successful one-hour completion

## Executable Guard

`tests/test_operator_runbook_policy_guards.py` pins the preconditions,
first-hour safety checks, abort conditions, rollback proof, and not-rehearsed
status so the paper-to-shadow checklist cannot silently become an automatic or
live-routing path.
