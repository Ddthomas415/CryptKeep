# Crypto-edge store ingestion: independent review (backlog item 9)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW. Patch 0053 (`58c49840`), bundle rev64,
folder `61_crypto_edge_capture_time`. Not pushed, not applied to this checkout.

## What holds

Numeric fields are validated as finite before insert; a bad row rolls back
its whole snapshot.

## Findings (shown by test; none has occurred in this checkout's data)

- **P2.** Capture time was not validated, and the funding context provider
  clamped a negative age to 0. The store selects the latest row by comparing
  `capture_ts` as text, so one future-dated funding row is selected every
  time and reads as fresh; `funding_extreme` would act on that one rate.
  Qualification rejects a capture later than the fill, so such fills would
  not count, but the signals and paper trades would still occur.
- **P3.** An unparseable capture time became the permanent "latest" row.
- **P3.** Mixed UTC-offset forms made text order differ from time order.
- **P3.** Rows with an empty symbol or venue were stored.
- **P3.** Open-interest `price_change_pct` was stored unvalidated.
- **P3.** A negative `strategy_context_max_age_sec` disabled the staleness
  check.

## Correction

Store: capture time must parse, is normalized to UTC, at most 300 s ahead of
the clock; symbol and venue required; `price_change_pct` validated.
Provider: `funding_context_capture_in_future` beyond 60 s; a zero or negative
age limit falls back to the 36 h default.

## This checkout's data (read-only)

- 62,730 rows: one capture-time form, none ahead of the clock, no empty
  symbol or venue.
- 3 of 23,501 quote rows have bid above ask (still accepted).
- Funding collection is about 46% of continuous: 11,471 snapshots in 86 days
  at a 311 s median spacing. Largest gaps: 215 h (from 08-14), 78 h (08-24),
  58 h (08-27). Belongs to backlog item 14.

## Verification

14 new tests, 12 fail on the previous code. Full suite at the code of 0053:
4667 passed, 33 skipped, 19 failed (the same 19 as master).

## Decision for the operator

Whether 36 h is the right freshness limit for an 8-hour funding rate.
