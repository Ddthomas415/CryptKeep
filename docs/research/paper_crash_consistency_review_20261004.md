# Crash consistency (live-money backlog item 4): paper path review

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0044 (commit 877401c2, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev55.zip`,
folder 52. Zip SHA-256:
57f1e328d024d9341f3045d5b27ef8513112da5ffc98c426fce833343fa93df4

Scope: the item's fault-injection suite covers the live path. This is the same
question on the paper path.

## What holds

The paper ledger applies order status, fill, position, cash and realized PnL in
one transaction. The trade journal is rebuilt from ledger fills by the runner's
reconcile step, so it converges after a crash.

## Findings (real engine and stores)

1. P2. The evidence fill record is written after the ledger commit,
   best-effort. With the process killed between the two, the ledger held both
   fills of a round trip and the position was flat; the evidence held only the
   buy. Nothing repaired it after restart. `EvidenceLogger._append` also
   swallows a failed write, so a transient write error does the same.
2. Consequence. With the evidence complete, 4 round trips were counted; with
   the first sell record missing, 0; with the first buy record missing, 3. One
   lost sell line stops the gate counting for good.

## This checkout (read-only)

20 ledger fills for BTC/USDT, 16 evidence fill records. The 4 without a record
are the two round trips of 2026-04-19, before the cohort. Every cohort fill has
its record.

## Correction in 0044

`PaperEngine.backfill_fill_evidence()` writes the missing record from the
ledger row and the order's stored meta, marked `evidence_backfilled: true`,
with the ledger fill time and no `pnl_usd`. The paper runner calls it once at
start. Only fills made since the engine first started under this code are
eligible, so existing history (including the four April fills) is never
rewritten.

6 new cases, 5 fail on the previous code. Full suite: 4567 passed, 33 skipped,
19 failed (the same 19 as master).

## Not changed

- The round-trip pairing still stops counting after a missing sell record.
- A write that fails mid-run is repaired at the next runner start.
- Order evidence records are not backfilled.
- The kernel's per-fill average counts a backfilled sell as 0.
