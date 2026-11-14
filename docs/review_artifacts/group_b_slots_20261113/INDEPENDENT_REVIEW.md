# Independent Group B source review

Bot relation: BOT_RULES. No current runtime configuration or operation verified.
Reviewer: Nash, separate agent, not an implementation author. No edits by reviewer.

## Plan review - 2026-11-14T04:03:04Z

INCOMPLETE as originally stated. Required explicit treatment of four boundaries:
invalid ranking versus cash selection; rotation independent of signal/warm-up/
latch; rejected durable exits and retired accounting; exact Monday00:05 validity,
common cutoff/ticker provenance/stable ties and same-week replacement rules.
The source increment implements these contracts without changing ranker weights.

## Initial source review - 2026-11-14T04:21:36Z

BLOCKED. Three reproduced findings:

1. BTC-labelled quote mapped/returned as ETH, price1000, emitted one BTC rotation
   SELL with reference1000. Canonical mapped identity missing. O-157.
2. SOL exit discovered while ranking missing stayed unresolved after flat;
   restored ranking permitted ETH BUY with managed symbols onlyBTC/ETH. Ownership
   discovery had not persisted independently of ranking acceptance. O-158.
3. A queued BTC BUY crossed Monday00:05 with no current ranking. The consumer
   called stub submission and reported submitted1 despite reader allow_buyfalse.
   This proves a submission-boundary bypass, not an actual fill. O-159.

The reviewer provided individual probe results. Its later combined reproduction
snippet was NOT rerun as a combined command. Author converted the three cases
into regression tests; all three failed before correction in1.40seconds.
Initial source copies and the initial ten-file checksum seal are preserved in
rejected_review/, rather than relabelled as accepted first-pass work.

## Correction requirements - 2026-11-14T04:25:48Z

Reuse paper_buy_terminal and order-status writes under the existing transaction;
expiry alone does not fence selection refusal. Preserve existing-order identity
and filled receipts. Do not nest a write transaction inside apply_fill. Recheck
at final logical commit; roll back provisional financial writes before writing
a durable refusal. Queue disposal must follow a terminal ledger receipt, never
precede it. The BUY being authorized must not veto itself as an open intent.

Author correction: canonical quote checks at rotation/fill; ownership persisted
before ranking checks; selection slot/rank/hash bound to the intent; checks at
consumer and engine (new/existing orders) and ledger. Final fill check uses a
savepoint on the same connection, rolls back provisional writes then atomically
persists terminal refusal. No false expiry timestamps or new retry controller.
Targeted original three regression cases passed after correction.

Reviewer separately clarified that unchanged-signal BUY nonretry is not an added
blocker when explicitly disclosed, and full cohort configuration remains a
separate activation requirement. Neither clarification waived the three defects.

## Correction-only review - 2026-11-14T04:36:24Z

BLOCKED, despite independently passing7focused cases (24deselected,0.96s).
The three original corrections were present. Reviewer found final authorization
I/O occurred AFTER the last quote/TTL check: advancing the clock6seconds during
the second authorization call committed one fill with a6000ms-old quote.
Ledger hash reviewed:00e8ad2073adf4d4bb7e2ed8e51cdac58da20090b97a87aba6d003f61d095ba6.
The source is preserved as rejected_review/paper_trading_sqlite_before_final_gate.py.

O-160 correction: return the checked ranking bounds, sample time after all final
authorization I/O, then check cached week validity, BUY age and quote freshness
with no further authorization I/O before logical commit. Three author regressions
(quote, TTL, week) each failed before and passed after the correction.

Author fault injection also found O-161: uncertain fence write aborted the batch
before other exits. Now the BUY stays unresolved and unrelated SELL processing
continues. Test first had an unsupported fixture argument (setup failure, not
behavior evidence), then reproduced the actual sqlite exception before the fix.
The timing/fault four-case selection passed1.10seconds. No false terminal state
or new retry policy was introduced.

## Final diff-only review - 2026-11-14T04:42:13Z

ACCEPTED_WITH_RISK for the reviewed source hashes. Reviewer independently reports
all3timing cases and the fence-error case passed, no remaining material blocker
in the reviewed corrections. No further loop started. Author's final consolidated
15-file run:606passed26.04seconds; not independently reproduced as a full selection.
Exact final-diff receipt, verified against current files at04:44:19Z:

```text
a9340633b45760a814ae64fdc9fa55a3c3b3f3e67ea3b236ed6cf9b62d6a9494  services/execution/paper_weekly_slot.py
d9142f603f11fec9ed4bb1b53971734a824893ffd0ff2334e91959eefdc5bde8  storage/paper_trading_sqlite.py
a1b385a408fb1494421901d50a9f868e300a3477342776f8596b95046de145da  services/execution/paper_runner.py
42a8232f761b4f2574901d43c0989ccc381bb2bd0b59ee176cf31f6953db79f3  tests/test_paper_weekly_slot.py
```

These are the final changed files in the correction-only review, not a claim that
the reviewer independently reran606tests or operationally verified the bundle.
The initial whole-increment inspection and subsequent correction reviews are
separate evidence from the author's eleven-file source/test integrity seal.

Source acceptance is not activation, commissioning, U-07 completion or financial
evidence. Actual operating configuration and quote/metadata availability remain
unverified.

What do I know that could change the owner's decision that I have not yet said?
Passing349focused author tests did not catch these three boundary failures.
Independent probes prevented acceptance of defective source; no deployment,
forward result or trading readiness follows even if correction review passes.
