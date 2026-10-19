# Maker versus taker execution: DRAFT v3 correction

Date: 2026-10-11. Active role: ENGINEER. Risk: HIGH (financial research methodology).
Acceptance: READY_FOR_INDEPENDENT_REVIEW. NOT FROZEN; no collection or execution authorized.

This is a new review draft, not an amendment to a frozen study. Preserve
`PREREGISTRATION.md` (v2) and `PREREGISTRATION_draft_v1.md` unchanged.
V2's conditional operator approval does not approve the new contract proposals below.
No orders, keys, trading, collectors, campaigns, infrastructure, or frozen studies change.

## Operator direction clarification (October 11 America/New_York)

The operator explicitly chose: "Preserve delayed execution; add arrival-book
observation." Therefore this draft retains A = actual T0 + 2 seconds and the
additional arrival-book requirement. The conflicting T0 exchange-time + 1 second
proposal (with 0/5 second sensitivities) in v2 is not silently substituted here.
Original v1/v2 documents remain preserved. This choice authorizes the design
direction, not a claim that arrival is observed, a numerical freshness tolerance,
study freeze, or economic scoring. An arrival receipt must retain request/receive
times, source timestamp where available, identity and clock uncertainty; unknown
alignment remains unknown rather than being inferred from a scheduled request.
The primary cost comparison must use the same qualified arrival book for both
methods. No valid arrival receipts were found in the bounded review.

The saved pair-preview request was incomplete: Coinbase returned
"account is not available". Product-specific fees remain UNVERIFIED; the observed
25/50 bps account tier may be named as a provisional sensitivity assumption only,
not confirmed product fees. No account change or real order is required or authorized
by this clarification. The remaining timing/source and fee evidence gates below stand.

## 1. Question and evidence lane

For BTC-USD and ETH-USD, does a hypothetical resting touch order with a taker
fallback reduce all-in implementation shortfall relative to immediate taker execution
at the SAME modeled arrival, quantity, and reference price?

All execution results are **CF-MODELLED**, not realized fills, profitability, or
execution readiness. Public prints describe actual other-party trades, not our order.
SHOWN in the source draft: a two-snapshot design and specified model rules.
UNVERIFIED: arrival eligibility, queue position, actual fills, and product-specific fees.

V2's economic illustrations remain context only: about 1.6 annual percentage points
per additional 10 bps per side at the stated turnover; a hypothetical 25 bps fee
saving is not an achievable saving or a reason to retain a server. Missed fills,
adverse selection, and implementation costs can erase it. Frozen strategy verdicts stand.

## 2. Unchanged design constants

- Primary sample: daily BTC and ETH BUY and SELL decisions, four events per day,
  each sized from a $500 reference notional; nominal maximum 224 events over 56 days.
- T0 target: 00:00:30 UTC, within the existing 120-second tolerance. Record the
  actual snapshot time; a late capture is not backdated to its target.
- Modeled arrival A = actual T0 + 2 seconds. T1 = actual T0 + 60 minutes.
  Preserve that original timeout definition; do not silently use A + 60 minutes.
- Three fill scenarios; strict trade-through remains the PRIMARY model, not a
  certified conservative bound. Queue-inferred and optimistic scenarios are secondary.
- Primary endpoint: mean D = maker-method cost minus taker cost, bps per side.
- Circular day-block bootstrap: 10,000 resamples, seed 20261011, primary block
  length 7 days; sensitivity lengths 3 and 14 days. All assets, sides and method
  pairs within each resampled day stay together; events are not independent samples.
- MAKER SUPPORTED: 95% CI upper bound < -10 bps. MAKER NOT WORTH IT: 95% CI
  lower bound > -10 bps. Otherwise INCONCLUSIVE. Secondary models cannot upgrade
  an unsupported primary result.
- Three consecutive validation days, discarded, with no cost/fill computation;
  then a fixed 56-day sample and one end analysis. No extensions, interim economics,
  replacement sources, parameter tuning, or shortening to meet a budget window.
- More than 10% event exclusions means DEGRADED and cannot be MAKER SUPPORTED.
  Report exclusions even below that threshold; missingness is not random by assumption.
- Actual Monday frozen-ledger trades remain a descriptive subset only; use their
  ledger-derived quantities identically in both methods, not the primary $500 sizing.

The daily balanced BUY/SELL primary sample is a hypothetical execution-cost panel,
not the weekly strategy's realized order distribution or a portfolio return series.
The weekly actual-ledger subset describes the strategy's decisions only; its maker
and taker executions are still CF-MODELLED, not actual fills. Do not extrapolate the
balanced-panel mean into weekly strategy savings without a separately justified
mapping of event timing, direction, size and turnover. No new weighting or threshold
is introduced by this clarification.

## 3. Venue and fee freeze gates

CLAIMED by v2: back-to-back public Advanced Trade and Exchange queries on October
11 returned matching trade IDs, with transient book differences. That observation
supports correspondence for those observations, not perpetual synchronization,
arrival-time equivalence, or identical endpoint latency. Retain raw receipts and
timestamps if available; their completeness has not been certified in this draft.

Intended sources remain Advanced Trade public product_book for L2 and Exchange
product trades for trade-ID coverage. Endpoint compatibility and timing must pass
validation. A mismatch is an exclusion/failed validation, not synthetic reconciliation.

**Fees remain PENDING before freeze:** BTC-USD maker and taker rates; ETH-USD maker
and taker rates; account/product applicability; discounts, subscriptions, promotions,
fee currency and fee calculation/rounding. Record the product, rates, effective time,
source and account applicability without exposing credentials. The October 8
account-level SPOT observation of 25/50 bps is not product-specific confirmation.

**SHOWN in the fresh saved observation:**
[`coinbase_fee_observation_20261011_review_followup_1.json`](../../../research/coinbase_fee_observation_20261011_review_followup_1.json)
records source observation time **2026-10-11T22:33:20.538294+00:00** (22:33 UTC),
status OBSERVED_ACCOUNT_SPOT_FEE_TIER, maker 25 bps and taker 50 bps,
has_promo_fee=false and has_cost_plus_commission=false. It records an existing
keyring-sourced private read-only request and orders_submitted=false; no new key,
login, or request is needed for this documentation correction. The raw response
was not saved, so this is evidence from the saved normalized observation, not
independent reproduction of the private response. Its product_specific_all_in_fees
and historical_fee_tier remain UNVERIFIED. The false account flags do not certify
BTC-USD/ETH-USD all-in rates or rule out every product-specific fee condition.
**Do not freeze from this account-only evidence.** Product-specific applicability,
all-in rates and fee conventions remain the gate above.

An operator UI record or separately authorized existing read-only preflight may
supply evidence; this document authorizes neither access nor a fee request.

Freeze the confirmed fee assumptions for the study. If the real tier changes,
report the divergence; the model is a fixed-fee comparison, not actual charged fees.
Product minimums and size/price increments also need a dated product source.

## 4. Arrival observability: proposed new contract, not approved

**Two snapshots at T0 and T1 cannot show the book at A = T0 + 2 seconds.** They
cannot establish whether a post-only order crosses at arrival, the arrival taker
VWAP, or the queue ahead at arrival. A stale T0 snapshot cannot prove rejection.
Trade prints alone cannot reconstruct intervening adds/cancels or executable depth.
Do not label unknown eligibility as filled, accepted, or observed rejection.

**DRAFT PROPOSED NEW CONTRACT:** obtain an arrival-aligned book observation, or a
validated reconstructable book stream covering A, in addition to T0 and T1. Capture
source event time where available, local request/receipt times and clock confidence.
Its acceptable freshness/alignment tolerance and handling of unavailable exchange
timestamps must be set and approved before freezing; no numerical tolerance is
invented here. A receipt at A is not proof the venue book was current at A.
This is a methodology prerequisite, not a request to build new infrastructure.

The actual observed/reconstructed book state at A must be known under that approved
time-alignment policy and retained with its provenance. Use that SAME arrival book
for post-only eligibility and the paired taker walk. A merely scheduled capture,
unknown-age receipt, or substituted T0/T1 book does not satisfy either requirement;
exclude both methods when the arrival state is unknown. This observes the historical
book only, not an actual order acknowledgement or guaranteed executable fill.

At A, BUY limit = T0 best bid; SELL limit = T0 best ask. Under the declared model,
BUY limit >= arrival best ask or SELL limit <= arrival best bid means post-only
rejection and full T1 taker fallback. Even this is modeled rejection, not an order
acknowledgement. Unknown arrival eligibility excludes the event; it is not a no-fill.
Only eligible events may consume post-arrival prints for modeled fills.

If the operator retains only two snapshots, arrival/taker execution and eligibility
remain unobservable: E1 cannot be frozen as an identified arrival-matched decision
test. A conditional T0-book proxy study would require its own explicitly approved
new contract and would not answer the same question. Do not silently substitute it.

## 5. Same base quantity, two methods

For each primary event define mid0 from the valid T0 bid/ask and base quantity
q = floor_to_product_increment(500 / mid0). Confirm q and both limit prices meet
product rules. This sizing formula is an explicit DRAFT contract clarification to
approve before freeze. BUY and SELL use q in both methods; do not independently
walk each book for $500 and thereby compare different quantities.

The taker baseline walks the opposite side of the arrival book for exactly q.
The maker scenario places exactly q at its T0-derived limit at A, remains active
without amendment until T1, and crosses only the residual q - filled_quantity
using the T1 book. Partial-fill arithmetic and fees operate on base quantity and
executed quote value. Both use mid0 as the common shortfall reference, so movement
between T0 and A is included equally. The baseline must not cross the T0 book.

Insufficient arrival depth for q or T1 depth for ANY possible residual up to q
makes the event excluded for both methods/scenarios. No last-level extrapolation,
invented liquidity, zero-cost residual, or different per-method sample is allowed.

## 6. Fill scenarios and queue limits

Only trades strictly after A and before T1 count as maker-window prints. Trades
at either boundary have ambiguous ordering and are not assigned a maker fill;
the T1 book supplies the fallback under the declared sequencing convention.
Confirm trade-side semantics before inferring aggressor direction; do not assume
an API's side field denotes the aggressor.

1. PRIMARY strict trade-through scenario: assign f = 1 at the first qualifying
   print below the BUY limit or above the SELL limit, conditional on eligibility,
   uninterrupted resting status, coverage and the price-priority model. Otherwise
   f = 0. **Full trade-through is not fill proof and not a guaranteed lower bound.**
   A historical book can trade through after actual orders cancel; our added order
   could alter the path. Halts, latency, hidden liquidity and priority rules also
   limit that counterfactual. Do not claim every hypothetical order was consumed.
2. Queue-inferred scenario: let Q_A be displayed same-side quantity at the limit
   in the arrival observation; f = clamp((V_at - Q_A) / q, 0, 1), or 1 when the
   strict trade-through scenario fires. V_at is eligible at-limit volume after A.
   Q_A and position are inferred, not an actual queue acknowledgement. Adds,
   cancellations, hidden/iceberg liquidity, aggressor-side uncertainty and
   counterfactual impact invalidate any guaranteed-conservative interpretation.
   Never count cancellation volume as fills. If Q_A/side information is missing,
   mark this scenario unavailable rather than inventing a queue.
3. Optimistic scenario: f = 1 at the first eligible at-or-through-limit print,
   else 0. This is an optimistic assumption, not a proven upper bound on realized
   fills. A tiny print can be smaller than q; it does not prove a full fill.

All scenario fill fractions are hypothetical and may include partial fills only
where the scenario specifies them. No public observation supplies a realized fill
for a nonexistent order. Full residual fallback remains part of every cost model.

## 7. Coverage, exclusions and validation

Retain append-only raw observations with hashes, product identity, timestamps,
pagination boundaries and fetch errors. Prove coverage of the entire [T0, T1]
trade interval, including both endpoints; consecutive IDs in an interior page do
not prove the start/end are covered. Deduplicate by product/trade ID; conflicting
duplicates, missing pages, unexplained ID gaps, or truncated endpoint history
exclude the paired event. A no-trade interval needs coverage evidence, not an
empty-response assumption. If IDs legitimately skip, a separately approved source
contract is required; do not silently waive the gap rule.

Require complete, ordered, noncrossed T0/arrival/T1 books with sufficient depth,
valid product increments, and the preapproved timestamp policy. Any arrival
observation/reconstruction gap excludes the event. Two endpoint books cannot prove
continuous book coverage; if no reconstructable stream is selected, disclose that
intermediate book evolution/cancellations are unobserved and never reconstruct
them from trade volume. Observed outage, halt or product-mode restriction excludes
the event; absent status evidence does not prove uninterrupted venue availability.

Apply one exclusion mask to all paired methods. Report reasons and counts by day,
asset and side, including unknown status and scenario-specific missing queue data.
Keep all 56 calendar-day positions in bootstrap blocks, including empty days; compute
the pooled mean over valid paired events in each resample. An empty resample is
undefined, not zero: its frequency must be reported and valid inference remains a
freeze/analysis gate. The partial-day handling here is a DRAFT contract clarification
for independent review, not permission to relax the >10% degradation rule.

Validation must establish timestamp/arrival observability, complete books and trade
coverage, stable source semantics, hashes, deterministic normalization and byte-identical
non-economic replay. No costs/fills during validation. The analysis and approved
contract are frozen before study day 1. Validation cannot certify future data health.
Three passing validation days do not guarantee 224 eligible events or adequate power.

## 8. Costs and defensible bounds

Let s = +1 for BUY and -1 for SELL. For base quantity x at VWAP P with fee rate r,
quote fee = x * P * r under the confirmed fee convention. For each method:

cost_bps = 10000 * [s * (sum(x * P) - q * mid0) + sum(quote_fee)] / (q * mid0).

For the maker method, one component is fq at the limit with maker fee; the other
is (1-f)q at T1 residual-depth VWAP with taker fee. The baseline executes all q
at arrival-depth VWAP with taker fee. SELL mirrors price shortfall, not fee signs.
Use confirmed fee currency/conversion and rounding rules; do not add a fee rate
directly to a price difference in dollars. D is the paired difference in these costs.

Always report scenario fill rates/fractions, D, asset/side breakdown, 95th percentile
maker-method cost, block sensitivities, descriptive Monday subset and exclusions.
MAKER SUPPORTED means only the frozen CF-MODELLED primary satisfies its threshold
and health gates; it does not certify fill advantage or realized profitability.

**Fill uncertainty:** without actual submitted orders, realized fill count is zero
observed orders and realized fill probability is UNVERIFIED, not estimated as a
certified interval. Conditional counterfactual fill quantity lies in [0, q]. Report
the no-maker-fill/full-fallback and full-maker-fill cost scenarios and, where useful,
the envelope over f in [0,1] using actual residual-depth walks. Do not assume that
only the two endpoints bound cost when depth/VWAP is nonlinear. These are finite
model sensitivity bounds only when the complete T1 depth and fixed price/fee
assumptions hold, not universal bounds on real execution loss.

**Adverse selection:** waiting shortfall is included but does not measure realized
post-fill adverse selection. An optional disclosed diagnostic is s * (limit - midT1)
/ mid0 * 10000 for each modeled maker fill, with its actual fill-to-T1 horizon and
quantity weighting. Positive is adverse to the maker. It is a modeled markout with
variable horizon, not a fixed-lag causal comparison. Two snapshots cannot produce
fixed-lag post-fill paths, intra-window worst excursions, or queue-cancel histories.
Any fixed-lag diagnostic requires a separately approved observation contract before
freeze; no such series or realized adverse-selection bound is claimed here.

## 9. Freeze, implementation and permitted consequence

Pending: independently reviewed arrival-data/timestamp contract, quantity/fee rules,
source coverage semantics, product fee evidence and deterministic sample/inference
handling. Operator must explicitly approve changed contract clauses. Hash the approved
registration and analysis artifact; no v3 approval is inherited from v2.

No collector or infrastructure is built by this correction. V2's two-run collector
description is insufficient for the proposed arrival observation and is not an
executable v3 plan. Cost and effort for any subsequent implementation require a
separate bounded decision. No validation/collection starts until the contract freezes.

A supported result may justify only a separately approved second paper ledger;
it never changes the frozen weekly test, enables orders, or demonstrates profit.
Remaining fee/sample/observability unknowns prevent freeze, not this documentation handoff.

Acceptance: READY_FOR_INDEPENDENT_REVIEW.
