# Canonical fill sink: independent review

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW, HIGH risk (live fill accounting). Patch
0059 (`c15d5664`), bundle rev70, folder
`67_fill_sink_loss_lock_and_risk_write`. Not pushed, not applied to this
checkout. Live is not enabled here.

Scope: `CanonicalFillSink`, where both reconcile paths hand every live fill:
journal, cost basis, daily loss figures, per-symbol consecutive-loss lock.

## What holds

Realized PnL is computed locally from a weighted-average cost basis, once per
(venue, fill id). A sell with no known position, an oversell, or a
non-positive quantity or price fails closed and writes the flag that blocks
new orders. The daily figures apply each fill once.

## Findings (shown by test: real sink, real sqlite stores)

- **P2.** The consecutive-loss symbol lock (default: 3 losses, 60 minutes)
  could not trigger in ordinary trading. The opening buy realizes 0, was
  treated as "not a loss", and reset the count. Three losing round trips in a
  row left the count at 1. No test covered this control.
- **P2.** The count was not once-per-fill. One losing fill delivered five
  times gave a count of 5 and locked the symbol.
- **P2.** `apply_fill_once` returns False both for "already applied" and for
  a failed write. The sink ignored it, so a failed daily-loss write returned
  `ok: true` and the loss was missing from the daily loss figure.
- **P3.** The flag writer raised when the data directory did not exist.

## Correction

- The count changes only the first time a fill's PnL is applied: loss +1,
  gain resets, zero no change.
- A fill not in the applied-fills ledger after `apply_fill_once` returns
  False is a failure (`risk_daily_apply_not_recorded`), flagged and retried.
- The flag writer creates its directory.

## Facts, not changed

- Only the legacy executor reads the symbol lock; the canonical consumer
  never does.
- The lock refuses sells too, so it can hold an exit for 60 minutes.
- A winning fill clears an active lock.
- A fill is counted on the UTC day it is reconciled.
- The daily loss limit sees realized losses only.
- A fee paid in the traded asset does not reduce the tracked position.

## Verification

8 new tests, all fail on the previous code. Full suite at the code of 0059:
4767 passed, 33 skipped, 19 failed (the same 19 as master).

## Decisions for the operator

1. Should the symbol lock block sells?
2. Should the canonical consumer honor the lock?
3. Should the daily loss limit include unrealized loss?
