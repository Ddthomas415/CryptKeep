# Live reconciler: independent review (deferred live-money item 4)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW, HIGH risk (live reconciliation). Patch
0057 (`194fa2ac`), bundle rev68, folder `65_reconciler_keeps_working_orders`.
Not pushed, not applied to this checkout. Live is not enabled here; none of
this has happened to real orders.

## What holds

The item's own claims: exactly-once venue submission, idempotent fill
accounting by fill id, the contiguous-prefix trade cursor, and the lookback
for a closed order whose fills are behind the cursor. The existing
fault-injection suite passes unchanged.

## Findings (shown by test: real sqlite stores, real loops, fake venue)

- **P1.** An order the venue still reports open or partially filled became
  the terminal `error` once older than `CBP_STALE_ORDER_MS` (default five
  minutes). Nothing cancels it and the reconciler scans only `submitted` and
  `submit_unknown`, so a later fill was never recorded in the trading store,
  the canonical journal or the daily risk figures. Limit orders are the only
  kind allowed by default.
- **P1.** One failed lookup of an order older than the same age made it
  terminal `error` the same way. The age is the order's, not the outage's.
- **P2.** A fee charged in anything but USD, USDT or USDC was recorded as 0
  with no trace. Fee-inclusive daily loss and journal PnL were understated
  by the whole fee.

## Correction

- Stale and still open or partially filled: stays `submitted`, marked once
  (`stale_open_order:<age>ms`), still reconciled.
- Stale and lookup failed: stays `submitted`, marked once, retried.
- Fee in the traded asset: valued at the trade's own price when the quote is
  a USD currency. Other non-USD fees: still 0, but flagged
  (`fee_usd_basis: unconverted`) and logged.

Contract change: `stale_open_order` and `stale_order_fetch_error` are
markers on a tracked intent, no longer terminal states.

## Not changed

`stale_order_not_found` is still terminal. Nothing cancels a stale order. A
venue-token fee is not converted. The legacy executor reconcile path was not
reviewed.

## Verification

15 new tests, all fail on the previous code (11 fee-table cases because the
function is new; four on behavior). Full suite at the code of 0057: 4753
passed, 33 skipped, 19 failed (the same 19 as master).

## Decisions for the operator

1. Cancel a stale open order automatically, alert on it, or leave it to you.
2. A price source for venue-token fees.
