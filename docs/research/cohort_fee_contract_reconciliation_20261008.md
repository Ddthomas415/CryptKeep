# Cohort and fee/PnL contract reconciliation

Date: 2026-10-08. AUDITOR. Documentation-only reconciliation; policy not activated.

## Current source evidence

SHOWN: configs/strategies/es_daily_trend_v1.yaml still declares promotion.paper.policy
cohort_start 2026-06-16T00:00:00Z, 45 days, 60 qualified bars and five qualified
round trips. These thresholds were not changed.

SHOWN: services/control/paper_evidence_qualification.py filters before-cohort
records and explicit source provenance, pairs completed cycles, then uses
fifo_pnl_from_fills for qualified net metrics. This inspected path does not
establish the recorded strategy's historical SMA/exit identity merely from its
strategy identifier. A source-qualified old-policy cycle is not corrected-policy
evidence. Exact current gate output was not rerun in this step.

SHOWN: storage/paper_trading_sqlite.py stores fee-inclusive buy cost basis and
subtracts the sell fee from proceeds; new fill output labels net_of_fees.
This implementation does not retroactively repair old average-price state or
historical records carrying inconsistent labels. Fee assets/currency conversion
and unsupported historical basis must remain visible.

The identity-correction analysis classifies June-July trades as legacy policy,
with zero qualified corrected-policy laptop cycles. The isolated host trial is
a different state/cohort and cannot silently replace canonical gate evidence.
The October 8 session reports zero trades; last direct host accounting check
was October 7. Historical identity classification not independently recomputed
in this documentation step.

## Recommended cohort contract - requires operator decision

Prefer a new, forward-only canonical analytical cohort beginning at a verified
runtime boundary, not a retroactive date selected from a commit or favorable PnL.
Record state directory, venue/symbol, loaded code, resolved SMA/ATR and exit policy,
entry contract, sizing, costs and source identity at that boundary. Keep prior
history intact and separately labelled. Do not reset warmup, entry latch or
positions; do not lower thresholds. Exclude cycles crossing an unverified policy
boundary from corrected-strategy evidence rather than assigning a guessed basis.

Alternatively, retain the existing gate configuration but explicitly regard it
as legacy-policy evidence, not corrected SMA200 acceptance. Historical reconstruction
can qualify records only if their actual matching runtime identity is proven.

No activation occurs here. Starting the isolated host trial September 12 does
not authorize changing the canonical laptop gate or combining their records.

## Recommended analytical net-PnL contract

- Gross PnL from matched actual entry/exit quantities and fill prices.
- Net trading PnL subtracts allocated entry and exit fees exactly once, plus
  applicable funding/borrow/conversion costs with timestamps and currency.
- Spread/slippage already embodied in actual fill prices are not subtracted a
  second time; report execution shortfall separately against a declared benchmark.
- Preserve gross, net, fee amounts/assets and basis/version fields. Unknown or
  inconsistent legacy labels require reconstruction from fills, not trust in text.
- Historical alternative fee tiers are MODELLED restatements, never rewritten
  actual fills. Record which account/product/order type the rate applies to.
- The trial's 7.5 bps fees/5 bps slippage remain its registered paper assumptions;
  do not change them mid-trial to the separately observed live fee tier.
- Operator infrastructure estimate approximately 20 USD/month is reported once
  at platform level; any strategy allocation is explicit, not automatically the
  full cost. Keep USD versus USDT conversion assumptions visible.

## Implementation consequences and required proof

Changing canonical cohort configuration or gate eligibility is HIGH risk and
requires separate review and explicit activation. First inspect current canonical
runtime ownership, positions and configuration; neither checkout identity nor a
date alone is sufficient. Tests must show legacy/wrong-policy/cross-boundary cycles
do not count, valid matching cycles do, original records are untouched, thresholds
are unchanged and fee allocation is not doubled. Any live fee change is separately
scoped; historical state migration is not authorized.

Reconciliation complete; activation decision INCOMPLETE. No source, gate config,
accounts, raw evidence, trial rules, process or service changed. No code tests run.
