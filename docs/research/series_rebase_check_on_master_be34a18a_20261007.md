# Review series checked against current master (be34a18a) - 2026-10-07

Status 2026-10-08: history. The current integration state is rev88 (`claude/series-rev34`,
72 commits on be34a18a); see the follow-up sections below.

Reviewer: Claude (AUDITOR). Done in a cloud clone of `Ddthomas415/CryptKeep`. Read-only
fetch of `origin/master`; nothing pushed. The series branch `claude/series-rev33`
(`7242a23b`, 73 commits on `97c24c8e`) is unchanged. The check used a separate local branch,
`claude/base-check-be34a18a`. No laptop source, state, campaign or config change.

## Why

Master moved after the series was cut: PR 605 (`dcf832e5`, durable ordered reconciliation
accounting) and PR 606 (workflow signing gates, desktop build paths). Master is now
`be34a18a`. The series had not been checked against it.

## Result

| Check | Result |
|---|---|
| Files changed on both sides | 5: the work log, `_executor_reconcile.py`, `fill_sink.py`, `execution_store_sqlite.py`, one test file |
| Series commits that conflict in code | 2 of 73: patch 0058 (`024023fb`, executor reconcile) and patch 0059 (`c15d5664`, fill sink) |
| Other 71 commits | Rebase onto `be34a18a` with no code conflict (work log merged by hand; all master entries kept) |
| Full suite, master `be34a18a` alone | 3877 passed, 33 skipped, 0 failed |
| Full suite, master + 71 commits | 4971 passed, 33 skipped, 5 failed |

PR 605 treats the same code as patches 0058 and 0059, differently. Those two patches cannot
be applied to master as written.

The 5 failures all come from leaving 0059 out:

- 3 in `test_repair_risk_sink_failed_clears_only_verified_causes.py`: patch 0065's repair
  script calls `RiskDailyDB.fill_applied`, which 0059 added.
- 2 in `test_place_order_symbol_loss_lock.py`: patch 0070's tests lock a symbol with three
  losing round trips, which only works with 0059's counting rule (below).

## Two defects 0059 fixed are still present on master (SHOWN by a direct probe)

Probe: master `be34a18a`, a temporary state directory, `CanonicalFillSink.on_fill` called
with paper values. No test file of mine involved.

1. **The consecutive-loss symbol lock cannot trigger across ordinary round trips.** Three
   losing round trips (buy 100, sell 99) leave `loss_count` at 1 and no lock. Each opening
   buy realizes 0 and resets the count with reason `reset_on_profit`
   (`apply_symbol_loss_fill_once`: `count = ... + 1 if pnl < 0 else 0`). PR 605 made the
   count exactly-once per fill; it kept the reset on zero.
2. **A failed daily-loss write is reported as accounted.** With the daily-risk write raising
   `sqlite3.OperationalError`, the sink returns `{"ok": True}`, the fill is absent from
   `risk_daily_fills`, the day's realized figure omits the loss, and no
   `risk_sink_failed.flag` is written.

Both are on the canonical fill path. Nothing produces live orders today, so no money is
exposed by either now.

## Patch 0058 against master

Its test file run against master: 3 pass, 4 fail. One failure is a helper only 0058 has
(`ExecutionStore.fill_totals`). The other three differ in behaviour:

- an order whose trade rows do not cover the venue's filled quantity stays
  `partially_filled` (0058 added the remainder from the order-level figures);
- a fee charged in the traded asset is recorded as 0.0 USD (0058 valued it);
- the journal-refused retry case.

PR 605's release note says it refuses unknown execution quantity and lists missing partial
fee evidence as outside coverage, so the first two may be intended. Not classified further.
This is the legacy executor, which has no producer.

## What this means for the series

- 71 of 73 patches carry over to current master unchanged in code.
- 0058 is superseded by PR 605 and should be withdrawn, with the three behaviour
  differences above put to the operator rather than re-patched by default.
- 0059 has to be rewritten on PR 605's structure: keep the count on a zero-PnL fill, fail
  the delivery when the daily-loss write is not in the ledger, restore `fill_applied`.
  0065 and 0070 depend on it.
- The review bundle (rev87) and REVIEW_GUIDE_0031_0075.md still describe the series on
  `97c24c8e`.

## Not done

- No rewrite of 0059 and no change to the series branch or the bundle.
- The laptop checkout's `origin/master` ref still points at `97c24c8e`; I did not fetch there.
- CI on the rebased branch: nothing is pushed.

## Follow-up, 2026-10-07: 0059 rewritten as patch 0076

Done on the local check branch `claude/base-check-be34a18a` (commit `df6a1c26`), not on the
series branch. Not pushed. READY_FOR_INDEPENDENT_REVIEW, HIGH risk.

- `apply_symbol_loss_fill_once`: a fill that realizes exactly 0 leaves the count and any
  lock unchanged and still records its event. Losses, profits, cutover, legacy identities
  and journal ordering are as PR 605 wrote them.
- `CanonicalFillSink`: a daily-loss write that is not in the applied ledger fails the
  delivery and writes the order-block flag; the flag writer creates its directory.
- `RiskDailyDB.fill_applied` restored (0065 uses it).

Full suite on master + 71 commits + 0076: 4989 passed, 33 skipped, 0 failed.
Tests: 13 cases in `tests/test_symbol_loss_lock_counts_closing_fills.py`; 7 of the 8
original 0059 cases fail on master `be34a18a`.

To know before accepting: a fill whose daily-loss write fails has no loss event, so PR 605's
ordering rule refuses later fills for that symbol until it is delivered again. The flag
blocks new orders meanwhile.

Patch, production-only diff and README: `docs/review_artifacts/20261004_rev32_bundle/patch_0076_on_be34a18a.zip`.
Patch 0058 is withdrawn. The rev87 bundle and review guide are not yet reissued on the new base.

## Follow-up, 2026-10-07: series reissued on be34a18a (rev88)

Branch `claude/series-rev34`, head `5b4ebb29c2c4e8bee33096aba64966ee6f40c25f`, local to the
review clone, not pushed. 72 commits on `be34a18a`: 71 carried over plus 0076. Code is
identical to the check branch; the work log now has the series entries on top and master's
log unchanged below.

Full suite at that head: 4989 passed, 33 skipped, 0 failed.
`git bundle verify` passes; `git am` of the 72 patch files on a clean `be34a18a` gives the
same tree as the head.

`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_series_on_be34a18a_rev88.zip` holds
the 72 patch files, a git bundle of the branch, PATCH_MAP.csv (old and new commit per patch)
and REVIEW_GUIDE_0031_0076.md. Per-patch READMEs stay in the rev87 bundle.
