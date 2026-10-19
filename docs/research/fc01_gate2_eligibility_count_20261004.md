# FC-01 gate 2: eligibility count - 2026-10-04

AUDITOR (Claude). Read-only. Counts timestamps, validity and the imbalance
feature only. NO return, price change or outcome was computed or looked at;
prices were read solely to apply the draft's validity rule (positive, finite,
ask >= bid). No collector started or stopped; no config, campaign or account
change. FC-01 remains an unregistered draft; this note registers nothing.

Draft counted against: `docs/research/faster_context_hypothesis_draft_20261004.md`,
SHA256 06587549bf1e5af70e4820b023ea7b03dd26e45db69adb2d1b131444ad41f97b.
Data: `.cbp_state/data/crypto_edge_research.sqlite` opened `mode=ro`,
`source='live_public'`, coinbase BTC/USD, `capture_ts >= 2026-08-30`.
7,790 book rows and 7,788 quote rows, 2026-08-30T07:59:04Z to
2026-10-04T00:06:13Z. First boundary 2026-08-30T12:00Z.

## Result under the draft as written (120-second freshness)

| Count | Windows |
|---|---:|
| Complete six-hour windows | 138 |
| Feature eligible: valid book snapshot at most 120 s before the boundary | 43 |
| Not eligible: latest snapshot older than 120 s | 95 |
| Outcome quote available: valid quote within 120 s after the next boundary | 47 |
| Feature eligible AND outcome quote available | 17 |
| Qualifying entries (imbalance >= 0.50), feature only | 9 |
| Qualifying entries with an outcome quote | **3** |
| ... that also have a quote within 120 s after the entry boundary | **0** |

No book or quote row fails the validity rule. The stored `imbalance` column
equals (bid_notional - ask_notional)/(bid_notional + ask_notional) on every
row (maximum difference 0).

## Why

SHOWN: the collector's cadence is about 311 seconds (median gap between
consecutive book rows 311 s, 90th percentile 312 s). Only 2 of 7,789 gaps are
120 s or shorter. A 120-second freshness limit therefore accepts a boundary
only when a capture happens to land in the two minutes before it: about
120/311, or 39%, of boundaries by chance, and the same again for the outcome
quote. Book and quote rows share a capture timestamp (7,785 of 7,790), so a
snapshot at most 120 s before a boundary and a quote at most 120 s after the
same boundary cannot both exist at this cadence.

There are also 55 gaps longer than one hour, the longest about 23 hours on
2026-08-31, so the 36 "days with data" are not 36 days of continuous capture.

## Sensitivity of the COUNT to the freshness limit (no outcomes)

| Freshness limit | Feature eligible | Outcome quote | Both | Qualifying, feature | Qualifying + outcome | + entry quote |
|---:|---:|---:|---:|---:|---:|---:|
| 120 s (draft) | 43 | 47 | 17 | 9 | 3 | 0 |
| 180 s | 67 | 67 | 51 | 11 | 7 | 1 |
| 330 s | 117 | 116 | 106 | 20 | 18 | 17 |
| 600 s | 121 | 119 | 111 | 20 | 19 | 18 |
| 900 s | 123 | 123 | 115 | 20 | 19 | 18 |

This table is about data availability only. It is not a tuning result and
must not be used to pick a limit after seeing outcomes; if the limit is
changed, that is a design revision to make and freeze BEFORE any outcome run.

## Reading

1. As written, the draft's pilot has 3 qualifying entries on the existing
   archive, and 0 if an entry-time quote within 120 s is also required. That
   is not a pilot sample.
2. The binding constraint is the mismatch between the 120-second freshness
   rule and the roughly five-minute collector, not the amount of data.
3. Even with a limit at or above the cadence (330 s or more), the archive
   holds about 18 qualifying entries in 35 days: roughly one every two days.
   The draft's power calculation (gate 3) has to be done on that rate, and a
   90-day confirmation interval at that rate would contain on the order of
   45 qualifying entries if capture stays as it has been.
4. The draft does not state which quote prices the entry. That needs to be
   fixed in the draft before gate 1, because at this cadence it decides
   whether any window is usable.

## Options for the draft's owner (not chosen here)

- Keep 120 s and collect faster. Needs a collector change, which is outside
  this note and outside current instructions ("don't start another
  collector").
- Set the freshness limit at or above the cadence and say so in the frozen
  rule, accepting that the feature is up to about five minutes old at the
  decision and that the outcome quote is up to about five minutes late.
- Conclude INSUFFICIENT_POWER for FC-01 on this archive and stop.

## Limits

Laptop archive only. `capture_ts` is taken as the availability time, which
the draft's gate 1 has not yet verified. Counts are of this archive and say
nothing about whether the imbalance feature has any value.

## Addendum - recommended treatment (same day)

AUDITOR recommendation for the draft's owner and the operator. Arithmetic on
the counts above and the draft's own cost input; still no outcome computed.

5. Fee load of the rule as drafted. With a freshness limit at or above the
   cadence the archive shows 18 to 20 qualifying entries in 34.5 days of
   windows, about 190 to 210 a year. Each is a market entry and a market
   exit. At the draft's scenario of 50 bps per side that is 100 bps per
   round trip, so **fees alone are about 190% to 210% of the entry notional
   per year** (about $190 to $210 a year on the draft's $100 entry), before
   slippage and infrastructure. For comparison the SMA200 candidate's 3.86
   round trips a year carry about 3.9% a year at the same rate.
6. Break-even. To be worth more than cash, the average six-hour move after a
   qualifying signal has to exceed 100 bps. That is a requirement on the
   MEAN of every qualifying trade, not on the good ones. No evidence in the
   repository suggests a five-level displayed-imbalance reading carries a
   directional edge of that size; the draft itself calls the mechanism
   unestablished. This is an a-priori cost argument, not a result.
7. Recommended treatment, in order:
   a. Do NOT start the 90-day confirmation collection for FC-01 as drafted.
      The cost hurdle in 5-6 should be faced first; it needs no new data.
   b. If the owner still wants FC-01 tested, revise the draft BEFORE any
      outcome run: (i) freshness limit at or above the collector cadence
      (330 s), stated as a frozen rule; (ii) name the entry price (first
      valid quote at or after the boundary, same limit); (iii) add a
      futility gate on the existing archive, which the draft already
      classes as exploratory: stop with no confirmation interval if the
      one-sided 95% upper bound on the mean gross six-hour return of
      qualifying entries is below the round-trip cost. With about 18
      entries that bound is wide, so passing it proves nothing; failing it
      saves 90 days.
   c. Reconcile the fee input. The draft calls 50 bps per side UNVERIFIED;
      the 2026-09-26 work-log entry records maker 25 / taker 50 bps from the
      authenticated Coinbase endpoint. Which is current decides 5-6.
   d. Carry the lesson to any later candidate: at this account's taker rate
      a rule that trades every day or two has to earn roughly twice its
      notional a year gross to break even. A candidate has to trade rarely,
      or be designed around resting (maker) orders with their own fill-risk
      model, or use a cheaper venue. Each of those is a separate registered
      question; none is proposed here.
8. Not recommended: speeding up the collector to satisfy the 120-second rule.
   It adds collection cost and delay to a rule that the cost arithmetic says
   is unlikely to clear its hurdle, and it is outside current instructions.

Decision owner: the operator (and Codex as the draft's DIRECTOR). Nothing in
this addendum was executed.

## Addendum 2 - fee input reconciled against the record (same day)

Read-only. Item 7c above asked which fee statement is current.

9. SHOWN: `docs/work_log/review_stabilized_work_log.md`, entry
   "2026-09-26: Separate-window breakout economic check", records "current
   maker rate 25 bps/side, taker 50 bps/side, no promotional fee reported"
   from Coinbase's authenticated SPOT transaction-summary endpoint, and adds
   "These are current rates, not proof of historical account rates."
10. So the 50 bps per side in the FC-01 draft is not unverified: it was
    verified for this account on 2026-09-26, eight days before the draft.
    The same entry says raw responses were not persisted and that the run
    had no independent review, so this is one recorded observation, not a
    reproducible one.
    What is NOT established: that the tier is unchanged today (Coinbase
    tiers follow trailing volume), and no raw response was saved, only the
    log entry. I did not re-query the endpoint; that needs the operator's
    credentials.
11. Effect on items 5-6: none. They use 50 bps per side taker, which is the
    recorded rate. At the recorded maker rate (25 bps per side, 50 bps round
    trip) the fee load would be about 95% to 105% of entry notional a year,
    but the draft excludes maker fills and a resting order is not
    guaranteed to fill.
12. Suggested wording for the draft: "50 bps per side taker, verified for
    this account on 2026-09-26 (work log); re-verify before any outcome run."

## Addendum 3 - the count made reproducible against the revised draft (same day)

Codex's rev41 review (`docs/research/rev41_checkpoint_review.md`) names
"FC-01 eligibility counting without outcome analysis" as the next economic
step. That count is this note; this addendum makes it re-runnable and pins
it.

13. The draft was revised after the count (fee wording only). Revised draft
    SHA256 0dba406c8da59394fd3854d4c987aa6148bb005b077da11550727cd311dacda9.
    Its entry rule, six-hour boundaries, 0.50 threshold and 120-second
    freshness and outcome limits are unchanged, so the count above applies
    to the revised draft as it stands.
14. Script: `docs/review_artifacts/20261004_fc01/fc01_gate2_count.py`,
    SHA256 8b020304556af82b0330b4dff33fe95c67e2d26a9605872e663832b677865244.
    Read-only (SQLite `mode=ro` plus `query_only`). It reads timestamps,
    validity fields and the imbalance feature; it computes no price
    difference, return or outcome.

    ```sh
    python3 docs/review_artifacts/20261004_fc01/fc01_gate2_count.py \
      .cbp_state/data/crypto_edge_research.sqlite
    ```
15. Pinned archive cut (the draft's gate 1 asks for exact rows): Coinbase
    BTC/USD, `source='live_public'`, capture_ts from 2026-08-30 through
    2026-10-04T00:06:13+00:00.
    - book rows 7,790, ids 229..8018, row-identity SHA256 (`id|capture_ts`
      per line) ed541b0d8b864a50e08f2f3becfba2dff87916ecba916e2d67bb1898ca0be34a
    - quote rows 7,788, ids 7679..23250, row-identity SHA256
      046ab36e59b7ea984e3b827ab6b070968ed34d0d3cac85c13e1bc96d46a9d98b
    The hashes cover row identity and capture time, not the price fields.
16. Re-run at 2026-10-04T15:48Z: every figure in the tables above
    reproduces (138 windows; at 120 s: 43 / 47 / 17 / 9 / 3 / 0; at 330 s:
    117 / 116 / 106 / 20 / 18 / 17).
17. Observation, SHOWN: an unpinned run at 15:48Z returns the same last
    capture, 2026-10-04T00:06:13Z. The laptop archive has received no
    Coinbase book or quote row for about 15.7 hours. Gaps this long have
    happened before (the longest earlier one was about 23 hours), so this
    is not by itself a fault, but the archive is not growing right now. I
    did not start, stop or inspect any collector.

Status of gate 2: DONE for the draft as written, result 3 qualifying entries
with an outcome quote (0 with an entry quote as well). The open item is not
more counting; it is the design choice in items 7-8 above, which belongs to
the draft's owner and the operator.
