# Pre-registration: maker vs taker execution for the BTC+ETH weekly rebalance

**Status:** DRAFT, awaiting operator approval. Nothing collects or runs until Damian approves.
On approval, this file's SHA-256 is recorded in the work log and the file is frozen. Any later change is a new, dated amendment.

**Scope:** research only. Public Coinbase market data. No orders, no keys, no account, config or campaign changes.
The frozen weekly paper test (`paper_btc_eth_trend_20261009`, 0.6% fee + 0.05% slippage) is **not modified** by this study.

## 1. Question
At the rule's rebalance time (Monday 00:00 UTC daily close), is a resting limit order at the touch materially cheaper than crossing the spread? The comparison is:

- **Maker:** 0.25% fee, with a taker fallback if the limit order doesn't fill.
- **Taker:** 0.50% fee.

The comparison is all-in, measured against the decision price, and includes the cost of non-fills and price run-away.

A lower maker fee does not by itself show that maker orders fill. This study measures fills directly.

## 2. Why it matters, and how much
The corrected stress results for 2024-26 show the rule's return falling by ~1.6 percentage points a year for every extra 0.10% of fee per side:
- at 0.50%: 23.1%/yr;
- at 0.60%: 21.5%/yr.

So the most a maker policy can save is roughly 25 bps per side, about **4%/yr of capital**. That is ~$40/yr at $1,000, against ~$240/yr of infrastructure. The result matters only at larger capital, or if infrastructure is cut. A positive result is not a profitability claim.

## 3. Data (public endpoints only)
Coinbase Exchange public REST:
- `/products/{BTC-USD,ETH-USD}/book?level=2`
- `/products/{id}/trades` (paginated)

**Feasibility check (2026-10-11 15:18 UTC):** both endpoints are reachable from the laptop VM. The BTC-USD spread was $0.01. About 1,000 trades arrived per ~9 minutes, so one hour of trades is roughly 5-15 pages.

**Assumption to verify before collection:** this public book is the same BTC-USD/ETH-USD book that Advanced Trade orders (the account with the 25/50 bps fee tier) would join. If it can't be confirmed, the result is labelled "Exchange-book proxy".

Two snapshots per event:
- **T0** = 00:00:30 UTC (within 120 s), L2 book: best bid/ask, size at the touch.
- **T1** = T0 + 60 min, L2 book. Every public trade between T0 and T1 is also fetched.

## 4. Events
- **Primary sample:** every day, for each asset, one hypothetical BUY at the best bid and one hypothetical SELL at the best ask.
  - That gives 4 events/day, ~224 events over the fixed 56-day period.
  - Daily rather than weekly is chosen for sample size. The time of day is the same as the rule's rebalance.
- **Confirmatory subset:** the actual rule trades on the Monday rebalances in the period (direction and size from the frozen paper ledger).
  - Expect fewer than 16. This subset is reported descriptively only, with no inference.
- **Hypothetical order size:** $500 notional, the largest single-asset change at $1,000 capital.

## 5. Fill rules (no queue-position knowledge, so two rules)
- **Conservative (PRIMARY):** filled only if a public trade prints strictly through the limit (BUY: trade price < bid0; SELL: trade price > ask0) before T1.
- **Queue-aware (secondary):** filled if the conservative rule fires, OR cumulative traded size at exactly the limit price after T0 is at least the T0 touch size plus own size.
- Partial fills are not modelled; a fill is all-or-nothing.

## 6. Cost metric
All costs are implementation shortfall, in bps, against **mid0** (the T0 mid), per side:
- **Taker:** (ask0 − mid0)/mid0 [mirrored for a SELL] + L2 depth walk for $500 + **50 bps** fee.
- **Maker policy:**
  - if filled: (bid0 − mid0)/mid0 + **25 bps**;
  - if not filled by T1: cross at T1, i.e. (ask1 − mid0)/mid0 + L2 depth walk at T1 + **50 bps**.
  - This captures non-fill cost and price run-away (adverse selection) against the decision price.
- **D** = maker policy − taker, per event. Negative means maker is cheaper.

## 7. Primary endpoint and decision rule (fixed now)
- **Primary:** the mean D on the primary sample, using the conservative fill rule and a 60-minute window.
- **Confidence interval:** 95% CI from a day-block bootstrap with 10,000 resamples and seed 20261011.
- **Practical threshold:** −10 bps. Above that, a change of execution isn't worth the complexity (10 bps × ~16x annual turnover ≈ 1.6%/yr).

| Outcome | Condition |
|---|---|
| MAKER SUPPORTED | CI upper bound < −10 bps |
| MAKER NOT WORTH IT | CI lower bound > −10 bps |
| INCONCLUSIVE | otherwise |

**Always reported:**
- the fill rate;
- D by asset and by side;
- the 95th percentile of maker-policy cost, as the tail risk of run-away;
- the queue-aware result;
- the confirmatory subset.

None of these can override the primary outcome.

## 8. Data health, exclusions and stopping
- **Excluded events:** any event whose T0 snapshot is more than 120 s late, whose T1 snapshot is missing, or whose trade pages have a gap (non-contiguous trade IDs). Exclusions are counted and reported.
- **Degradation:** if more than 10% of events are excluded, the study is DEGRADED and the outcome cannot be MAKER SUPPORTED.
- No replacement or backfilled data from other sources.
- **Fixed length:** 56 days, starting on the first full UTC day after the collector is approved and its first run is verified.
- **One analysis, at the end.** Interim checks are data-health counts only, with no cost results.

## 9. What a result can and cannot change
- A MAKER SUPPORTED outcome can only justify a separately approved change: a second paper ledger at 0.25% plus the measured non-fill cost.
- It does not change the frozen paper test, authorize live maker orders, or support any profitability claim.

## 10. Implementation, after approval (not built yet)
- One stdlib collector script, using public endpoints only, with two daily scheduled runs on the laptop:
  - 00:00 UTC: T0 snapshot;
  - 01:01 UTC: T1 snapshot and trades.
- Append-only JSONL output, plus one analysis script that runs once at day 56.
