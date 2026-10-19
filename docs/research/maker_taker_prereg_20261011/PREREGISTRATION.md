# Pre-registration: maker vs taker execution for the BTC+ETH weekly rebalance (DRAFT v2)

**Status:** DRAFT v2. Methodology conditionally approved by the operator on 2026-10-11.
**NOT FROZEN:** freezing waits on the pair-specific fee confirmation in section 3. Nothing collects or runs before the freeze.
- On approval, this file's SHA-256 is recorded in the work log and the file is frozen. Any later change is a new, dated amendment.
- v1 is kept in `PREREGISTRATION_draft_v1.md`.
- v2 changes (from the operator's review):
  - three fill rules with partial fills;
  - venue checked against data;
  - a fee check required before freezing;
  - a time-aware bootstrap that keeps pairs together;
  - a validation phase;
  - fixed timeout.

**Scope:** research only. Public Coinbase market data. No orders, no keys, no account, config or campaign changes.
- The strategy and the frozen weekly paper test (`paper_btc_eth_trend_20261009`) are **not modified**.
- Execution is the only variable being tested.

## 1. Question
At the rule's rebalance time (00:00 UTC daily close), does a resting limit order at the touch reduce the all-in cost of trading, compared with crossing the spread?
- All-in cost includes the fee, spread, price movement while waiting, and any unfilled amount.
- The reduction has to be large enough to matter.

## 2. Economics (context, not a reason to keep infrastructure)
- From the corrected 2024-26 stress results, each extra 0.10% of fee per side costs ~1.6 percentage points a year: 23.1%/yr at 0.50%, 21.5%/yr at 0.60%.
- The maximum fee saving is 25 bps per side, about 4%/yr. That's ~$40/yr at $1,000, against ~$240/yr of server cost (a gap of about −$200).
- Missed fills and price run-away can shrink the saving or make it negative.
- A positive result is not a profitability claim, and it doesn't justify keeping any infrastructure.
- The value of the server to other research work is a separate decision.

## 3. Venue, product and fee checks
**Venue: checked on 2026-10-11 at ~15:25 UTC.** These public, no-key endpoints were queried back to back for BTC-USD and ETH-USD:
- Advanced Trade: `api.coinbase.com/api/v3/brokerage/market/product_book` and `/ticker`;
- Coinbase Exchange: `/products/{id}/book` and `/trades`.

Result: they returned **identical trade IDs** (e.g. BTC 1104711568-70, ETH 847929902-04), so they are the same matching engine and order book. The Exchange book endpoint was briefly staler (top of book differed for up to ~1 s).

Therefore:
- **Book snapshots** come from the Advanced Trade public `product_book`, which is the API the account trades on.
- **Trades** come from the Exchange `/products/{id}/trades`, which has contiguous integer trade IDs for checking gaps.

**Fee: required before freezing.** The account tier was observed on 2026-10-08 as 25 bps maker / 50 bps taker per side. Applicability to the BTC-USD and ETH-USD products was still pending verification.
- Before the freeze, Damian confirms, either in the Coinbase UI or with the existing read-only fee preflight (Claude reads no keys):
  - (a) BTC-USD maker and taker rates;
  - (b) ETH-USD maker and taker rates;
  - (c) any discount, promotion, subscription or account-specific condition that changes them.
- The confirmed values and their source are written into this section before hashing.
- The Oct 8 reading (`research/coinbase_fee_observation_20261008.json`) is account-level SPOT only. It marks product-specific fees UNVERIFIED and does not satisfy this gate.
- If the tier differs, the confirmed rates replace 25/50 here before the freeze.
- Tiers depend on 30-day volume, so the confirmed rates are fixed for the whole study.

## 4. Events (one decision, two execution methods)
**Primary sample:** each UTC day, for each asset:
- one hypothetical BUY of $500 notional resting at the best bid;
- one hypothetical SELL of $500 notional resting at the best ask.

That is 4 events/day, ~224 over 56 days. $500 is the largest single-asset change at $1,000 capital.
- The time of day is the rule's rebalance time; daily rather than weekly is for sample size.

**Paired:** for every event, the taker and maker results are both computed from the same reference timestamp, quantity, and market data.

**Confirmatory subset:** the actual Monday rule trades in the period.
- Direction and quantity come from the frozen paper ledger, with $ amounts scaled to its equity.
- This subset is reported descriptively only.

## 5. Snapshots and fill rules
**Snapshots:**
- **T0** = 00:00:30 UTC (must be within 120 s): L2 book to a depth that covers $500 plus the size at the touch. The book's own exchange timestamp is recorded as **t_book**.
- **Arrival is observed, not assumed (amendment, 2026-10-11).** The hypothetical order's limit is the touch in this same T0 snapshot, and its arrival time is t_book.
  - Two snapshots cannot reconstruct the book at an unobserved later instant, so no "T0 + 2 s" book is used.
  - Trades count toward a fill only if their exchange time is after t_book plus a latency allowance.
  - The latency allowance is 1 s for the primary analysis. Sensitivity runs use 0 s and 5 s.
  - The first counted trade ID is recorded for each event.
- **T1** = T0 + 60 min: L2 book. All trades between T0 and T1 are also fetched.
- **The 60-minute timeout is fixed.** No other timeout is analysed for the decision.

**Eligibility assumptions (apply to all three rules).** A public trade shows a fill only if the hypothetical order would have been eligible and resting at that moment. The model assumes:
- **Arrival:** at t_book plus the latency allowance, on the same product (BTC-USD or ETH-USD) and side. Trades at or before that moment are ignored.
- **Price at arrival:** it is a post-only limit at bid0 (BUY) or ask0 (SELL), taken from the T0 snapshot. If any trade within the latency allowance prints through that price, the book may have moved before arrival. In that case the order is treated as rejected (it would have crossed), and the whole event goes to the taker fallback at T1.
- **Active until T1:** the order stays active, is not cancelled or amended, and has no time-in-force expiry before T1.
- **Exchange rules:** $500 meets product minimums and size increments. Self-trade prevention is not relevant, since no orders of ours exist.
- **Limits of the model:** venue outages, trading halts or post-only-only modes in the window make an event excluded, not filled. Hidden or iceberg liquidity is not modelled.

**All fills are MODELLED.** No order is placed, so a public trade, even one strictly through the limit, is evidence consistent with a fill, not proof of one. Every fill field in the outputs and the report is labelled `modelled`. The conservative rule is the most defensible model, not an observation.

Three fill estimates, all reported. Partial fills are allowed where the rule gives a fraction.

**1. Conservative (PRIMARY): trade-through (modelled).** The order is modelled as fully filled at the first public trade strictly through the limit after arrival.
- For a BUY that means a trade price below bid0; for a SELL, above ask0.
- Under price-time priority, a print through the limit means everything resting at the limit was consumed or cancelled, and that includes this order.
- It ignores fills that happen at exactly the limit price, so it understates the fill rate.

**2. Queue-aware: estimates partial fills.** Fill fraction = clamp((V_at − Q0) / own_size, 0, 1), or 1 if rule 1 fires.
- V_at is the traded size at exactly the limit after arrival, and Q0 is the size at the touch in the T0 snapshot.
- It ignores cancellations ahead of this order, which makes it conservative about queue position.

**3. Optimistic: upper bound only.** The order is fully filled at the first trade at or through the limit.

**Fallback:** any unfilled quantity at T1 is crossed as a taker at the T1 book.

## 6. Cost: implementation shortfall vs mid0, bps per side
For a SELL the signs are mirrored.
- **Taker:** walk the T0 book for $500, minus mid0, plus the taker fee.
- **Maker method:**
  - filled fraction f: (limit − mid0) + maker fee;
  - unfilled (1 − f): walk the T1 book − mid0 + taker fee.
  - So the cost of waiting, price run-away and unfilled amounts is all included.
- **D** = maker method − taker, per event. Negative means maker is cheaper.

## 7. Primary endpoint, inference and decision rule
**Primary:** the mean D on the primary sample, using the conservative fill rule.

**Inference: circular block bootstrap over days.**
- 10,000 resamples, seed 20261011.
- The resampling unit is the whole day: all four events, both assets and both sides, stay together, which preserves their correlation.
- Primary block length is 7 days. Sensitivity runs use 3 and 14 days.
- No observation is treated as independent.

**Threshold:** −10 bps per side. That is ~1.6%/yr at about 16x annual turnover, the smallest saving that justifies the added operational complexity.

| Outcome | Condition |
|---|---|
| MAKER SUPPORTED | 95% CI upper bound < −10 bps |
| MAKER NOT WORTH IT | 95% CI lower bound > −10 bps |
| INCONCLUSIVE | otherwise |

**Always reported:**
- fill rate and mean fill fraction under each of the three rules;
- D under each rule;
- D by asset and side;
- 95th percentile of maker-method cost (tail risk);
- block-length sensitivity;
- the confirmatory subset.

The queue-aware and optimistic results can only show how fragile the result is. They **cannot** turn the primary outcome into MAKER SUPPORTED.

## 8. Validation, data health and stopping
**Collector validation:** 3 consecutive days before the study starts. It checks:
- timestamps;
- snapshot completeness;
- trade-ID continuity from T0 to T1;
- byte-identical re-analysis of the same raw files.

No costs or fills are computed during validation. Validation days are discarded and do not count toward the 56.

**Exclusions:** an event is excluded if its T0 snapshot is more than 120 s late, its T1 snapshot is missing, or its trades have an ID gap. Exclusions are counted.
- If more than 10% of events are excluded, the study is DEGRADED and cannot be MAKER SUPPORTED.
- No replacement data from other sources.

**Fixed length:** 56 days, starting on the first UTC day after validation passes. There is one analysis, at the end. Interim checks are data-health counts only.

**No tuning:** the timeout, fill rules, size and threshold are fixed by this document.

## 9. What a result can and cannot change
- MAKER SUPPORTED can only justify a separately approved, second paper ledger at the confirmed maker fee plus the measured non-fill cost.
- It does not change the frozen paper test, enable live or maker orders, or support any profitability claim.

## 10. Implementation, after approval (not built yet)
- One stdlib collector, using public endpoints only, with two daily scheduled runs on the laptop:
  - 00:00 UTC: T0 snapshot;
  - 01:01 UTC: T1 snapshot and trades.
- Append-only raw JSON files, with a SHA-256 manifest.
- One analysis script, written and frozen before day 1 of the study and run once at day 56.
