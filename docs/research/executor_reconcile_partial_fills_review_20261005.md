# Legacy executor reconcile: independent review (deferred live-money item 4, continued)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW, HIGH risk (live reconciliation). Patch
0058 (`024023fb`), bundle rev69, folder `66_executor_reconcile_partial_fills`.
Needs 0057. Not pushed, not applied to this checkout. Live is not enabled
here.

Scope: `live_executor.reconcile_live` (`_executor_reconcile.py`), the path
0057 said it had not reviewed.

## What holds

Trade rows are deduplicated per intent by trade id. A failed order lookup
leaves the intent tracked. No submit is made from this code.

## Findings (shown by test: real ExecutionStore, fake venue)

- **P1.** The pass lists intents in `submitted` and `pending`. On an order's
  first partial fill it sets the intent to `partially_filled`, which is not
  in that list, so the order is never looked at again: remaining fills are
  not recorded and it never becomes `filled`.
- **P2.** The execution-store row was written before canonical/risk
  accounting and the accounting result was ignored. A fill the journal
  refused was still counted and never offered again. One existing test
  depended on this.
- **P2.** Non-USD fee recorded as 0, as in 0057.
- Follows from fixing P1: the order-level fallback added the whole filled
  quantity even when part was already recorded trade by trade.

## Correction

- `partially_filled` is listed for reconcile.
- Accounting first, store row second; a refused fill is retried and the
  intent is not marked `filled` in that pass.
- The fallback adds only the quantity not yet recorded
  (`ExecutionStore.fill_totals`).
- Fee valued by the function from 0057.

## Verification

6 new tests, 5 fail on the previous code (the sixth is a control). One
existing fixture now stubs the sink. Full suite at the code of 0058: 4759
passed, 33 skipped, 19 failed (the same 19 as master).

## Decision for the operator

Two live paths exist: the canonical consumer + reconciler, and this legacy
executor. Each fix has to be made twice. Which one is meant to run?
