# Stage promotion and the capped-live gate: independent review (deferred live-money item 14, continued)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW, HIGH risk (promotion gate; the change
only makes the gate harder to pass). Patch 0063 (`9ebc4cf2`), bundle rev74,
folder `71_capped_live_gate_scope`. Not pushed, not applied to this checkout.

Scope: the stage store, the promote command and the gate that authorizes it.

## What holds

- `promote()` moves one step at a time, refuses from safe-degraded, needs its
  operator event and restores the stage file when the event cannot be written.
- The promote command asks the gate first and fails closed.
- `ready` is false while a manual review item is outstanding.
- A corrupt or missing stage file reads as paper, the least permissive stage.
- The shadow gate counts only shadow-stage records since the stage began.

## Finding (P2; probe and test with the real stage store, evidence logger and `run_check`)

The capped-live gate authorizes the step to scaled live (full allocation). It
read every record ever logged. With 25 paper round trips and no live fill, on
the previous code:

| Gate | Result |
|---|---|
| 20+ completed live round trips | passed, "25 round trips" |
| Expectancy holding within range of shadow | passed |

The only gate tied to the stage was the 8-week timer. The code labelled this
scope `legacy_all_evidence`; no backlog or work-log entry mentions it.

## Correction

The capped-live gate uses the same selection as shadow: only records stamped
`capped_live`, logged since the stage began, count. Requested before the
stage begins, nothing counts.

## Not changed

Paper and shadow gates; the thresholds; "Position size at 25% of intended" is
still reported passed without a check; 0.0 weeks at a stage displays as
"unknown"; expectancy still averages every fill row with a `pnl_usd`.

## Context

Nothing produces live orders today, so no capped-live evidence exists and this
gate has never been evaluated for real.

## Verification

4 new tests, 3 fail on the previous code. Full suite with the tooling on the
right interpreter: 4805 passed, 33 skipped, 0 failed.
