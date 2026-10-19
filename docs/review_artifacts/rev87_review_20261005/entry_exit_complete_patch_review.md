# Complete patches 0016-0018 - 2026-10-07

Active role: AUDITOR. Overall acceptance INCOMPLETE.

All 1,964 lines of the three complete patches were read in contiguous ranges,
including production changes, test bodies, work-log additions and trailers.
This extends the earlier diff-only review; it does not replace independent
acceptance or establish deployment, actual fills or profitability.

## Findings and preserved decisions

- SHOWN, 0016: tests cover all four in-flight statuses, buy and sell rows,
  terminal statuses, symbol/source separation, unreadable lookup, entry-state
  timing and risk-block ordering. A real SQLite query test places an open row
  behind 250 filled rows. Runner-level cases use doubles; these are different
  proof lanes. The unreadable-queue recovery test explicitly expects no retry
  after the signal was consumed. This is disclosed inherited behavior, not
  approval to change the documented crossover strategy.
- SHOWN, 0017: tests cover repeated blocked losses, stop-loss, time and
  trailing-stop preservation, flat-position cleanup and existing sell-scan
  behavior. They do not tie stop state to a position identity or cover an
  external close/reopen without an observed flat turn. The work log discloses
  that gap and changed sell outcomes. Its original claim that a sell was
  recorded only when written is explicitly withdrawn by 0018.
- SHOWN, 0018: the transaction test checks all-or-nothing state changes, but
  the runner still used separate queue/state stores and one pending plan.
  Its whole-queue-unreadable test EXPECTS two sell intents but loss streak 1.
  That test documents an unsafe under-count; a passing test is not evidence
  that the required performance kill was preserved. Later journal recovery
  supersedes this implementation; do not relabel it as a new current defect.
- SHOWN: several historical descriptions/tests call these counters realised
  PnL or real losing exits despite using reference-price intents and simulated
  positions. 0018 expressly corrects the contract to provisional intent-time
  figures. Preserve that correction in economic reporting.
- SHOWN in latest candidate strategy_runner.py:384-403: the normal exit scan
  still examines the newest 200 rows, recognizes queued/submitted only and
  returns false on read failure. This previously recorded limitation remains;
  it is not fixed by entry lookup or exit-event durability. No new actual
  duplicate order/fill or campaign occurrence is claimed here.

## Verification limits

No tests were executed in this slice. Test assertions and fixture behavior
were inspected, not promoted to fresh passing results. Candidate fixture
imports and inherited database overrides need explicit isolation before a
runner test run; CBP_STATE_DIR alone is not sufficient evidence of safety.
The real-queue tests are present in the supplied code, not rerun proof.

No production, config, account, campaign, background process or deployment
changed. No new current defect reproduced. Previously reproduced findings
remain open; this slice does not provide an all-clear.

## Exact full-read artifacts

Paths relative to extracted cryptkeep_review_bundle_2026-10-02.

| SHA256 | Artifact |
| --- | --- |
| `9f2b443f0649d500386509e127d8c181ed958f24f711a41e7f54355c90e292d5` | `23_entry_open_intent_fix/0016-fix-entries-are-refused-while-any-strategy-intent-fo.patch` |
| `e34ee580666204281a922a5deb7b142a4d166640ca6daaf07e1d108e07ebcbe7` | `24_held_back_exit_bookkeeping/0017-fix-an-exit-held-back-by-an-open-intent-records-no-e.patch` |
| `f661544783e57f9e79cea488c7afcfcbf3284e41e2f20744656c3b9b80f0a220` | `25_exit_accounting_event/0018-fix-exit-counters-are-recorded-once-after-the-sell-i.patch` |
