# CryptKeep Execution-Cost Research Policy

Status: `POLICY_DOCUMENTED`

## Purpose

Define the research-only path for maker-vs-taker, fee-tier, venue-cost, and
limit-fill-probability analysis. This document does not change order routing or
paper/live order type behavior.

## Current Boundary

SHOWN:

- Paper and backtest code already model fee/slippage at a basic level.
- Shadow would-be-fill evidence is the intended source for real spread and
  slippage measurement.
- Backtest/evidence windows already track slippage sensitivity.

UNVERIFIED:

- No accepted maker/taker cost-stack report exists.
- No venue fee-tier comparison is a promotion gate.
- No limit-fill probability model has been validated from stored shadow data.

## Current Tooling

`scripts/report_execution_cost_stack.py` is the research-only report consumer
for stored `shadow_would_be_fill` records. It is read-only, excludes normal
paper fills, and writes no trading, routing, or campaign state.

Current boundary:

- taker cost is computed from modeled shadow fill price, reference mid, and
  recorded fee bps;
- maker-side output is quote-only unless records also include
  `subsequent_price_path`;
- without enough stored subsequent-path records, the recommendation must remain
  `research_more`;
- `candidate_execution_policy_change` is possible only from path-backed shadow
  records and still requires separate high-risk execution-policy review.

## Research Data Required

The research report must be reproducible from stored records containing:

- venue, symbol, strategy, stage, and timestamp;
- intended side and quantity;
- contemporaneous bid, ask, mid, spread bps, and depth where available;
- modeled taker fill price;
- modeled maker/resting price;
- subsequent price path used for fill-probability estimation;
- fee schedule or explicit fee assumption;
- resulting cost stack in bps.

## Hard Constraints

- Research only until strategy expectancy is proven after measured costs.
- No live order-routing changes from this work.
- No canonical paper campaign order-type change from this work.
- Maker-side conclusions must come from shadow records or an explicitly
  reviewed engine extension, not from assumptions about current paper fills.
- Any future execution-policy change requires a separate high-risk review.

## Proof Required

Gap closure requires one accepted report showing:

- per-venue maker and taker cost stacks in bps;
- fill-probability estimates for modeled maker orders;
- sensitivity of strategy expectancy to cost assumptions;
- source data hash or artifact path;
- explicit recommendation: `no_change`, `research_more`, or
  `candidate_execution_policy_change`.
