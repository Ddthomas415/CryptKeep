# Edge collector cadence: independent review (backlog item 14)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW. Patch 0054 (`986817a9`), bundle rev65,
folder `62_edge_cadence_source_and_gaps`. Not pushed, not applied to this
checkout. Hetzner was not reachable from the review session and not checked.

## What holds

The checker opens the store read-only, fails closed on a missing or
unparseable newest snapshot, and its alert dispatch cannot raise.

## Findings

- **P2 (test).** The checker read the newest snapshot of any source, so
  loading the sample bundle or recording a manual snapshot made a dead
  collector read as fresh.
- **P2 (test).** A row the store refuses in one family raised out of
  `collect_once`; the families after it in that cycle were not written.
- **P3 (test).** A newest snapshot dated in the future read as fresh.
- **Data.** The checker looks only at the newest snapshot, so it cannot
  report cadence gaps, which the item asks for.

## This checkout's data (read-only)

| Measure | Value |
|---|---|
| Holes in live funding longer than the 12 h alert threshold | 8, longest 215 h |
| Open interest and order books, 2026-07-12 to 2026-08-10 | nothing stored (funding and basis were) |
| Funding, last 30 days | 94.5% covered, 11 holes over 1 h, longest 15.9 h from 2026-10-04 00:06 |
| Funding, last 7 days | 84.8% covered, 2 holes over 1 h |

The cause of the missing open-interest month was not established. No
scheduled run of the checker was found on this machine, and alerts are
disabled here.

## Correction

- Checker: `live_public` rows only (`--source`, `any` for the old behavior);
  future-dated newest snapshot is `missing`; a 7-day `history` block per
  family that does not change `ok` or the exit code.
- Collector: families stored independently; `store_errors`,
  `failed_checks`, `degraded`; `partial_store_failure`.
- Contract change: a store with only non-`live_public` rows now reports
  those families missing.

## Verification

5 new tests, all fail on the previous code. Full suite at the code of 0054:
4672 passed, 33 skipped, 19 failed (the same 19 as master). The history
figures come from a short read-only script with the same arithmetic, not the
patched module.

## Decisions for the operator

1. The 12 h alert threshold against a 5-minute collector.
2. Whether this machine or Hetzner is the collector of record.
