# E1: current freeze gaps and reuse boundary

2026-10-28. Active role AUDITOR. E1 freeze INCOMPLETE.
Scope: the existing execution-cost study, not a new strategy or study activation.

## Practical Answer

E1 still cannot start its registered validation. "Waiting on fees" is incomplete:
the current v3 draft also requires reviewed arrival-time qualification, source
coverage, quantity/fee rules and inference handling. Its collection is not supplied
by the running defaults-25 candle pilot or by the existing shadow-cost reporter.
Do not build another general research framework to hide these specific gaps.

The full288-line v3 draft and full109-line budget were read. Budget dates are
SHOWN planning targets: fee confirmation by November3; three discarded validation
days followed by a full56-day sample starting by November7 for this reporting
window. A late start moves the report; it does not shorten the sample or allow
backdating. These dates are not an activation deadline that overrides readiness.

## Current Evidence

- `maker_taker_prereg_20261011/PREREGISTRATION_draft_v3.md` is explicitly NOT
  FROZEN and READY_FOR_INDEPENDENT_REVIEW. Preserve it and its earlier drafts.
  The operator already selected delayed execution with an additional arrival
  observation. Do not re-ask that choice or substitute a T0-only proxy.
- The budget's E1 status still names conditionally approved v2 and only fees.
  The later v3 draft and October11 work-log clarification describe the additional
  gates. This note supersedes that short status for planning, not the fixed
  registered outcomes or the original budget artifact.
- Saved normalized account-fee observation is dated October11, not current
  product-specific proof. The saved product-preview record remains
  PREVIEW_LOOKUP_INCOMPLETE, orders_submitted=false. The original work log
  records account-availability rejection, not a demonstrated sign-in problem.
  No new account request or credential access was made here.
- Both saved October12 BTC/ETH arrival diagnostics retain initial/arrival raw
  bodies. All four Base64 bodies match their recorded SHA256 and parsed payload;
  product IDs and local request/receive ordering match. Their clock uncertainty
  and arrival alignment remain UNVERIFIED, scoring_authorized=false. Valid hashes
  do not qualify an old book as current or prove exchange/local clock alignment.

## Reuse The Existing Components, Without Re-labelling Them

`scripts/research/observe_coinbase_arrival_book.py` already captures T0 and a
second public book, with raw bytes/hash/local clocks. Its target is explicitly
T0 local receipt plus2seconds. It does not implement T1 at60minutes, interval
trade pagination/coverage, continuous product-status evidence, three-day
validation, a56-day schedule or the E1 paired analysis. Its existing delayed
observation is useful, but not a complete or qualified E1 data path.

`services/strategies/market_context_capture.py` and its v0 documentation provide
bounded observe-only diagnostics from existing runner quotes. Exchange event
and receipt timestamps are absent in that v0 contract, coverage unverified;
BUY-only candidate records and dropped/pending events cannot supply the balanced
E1 BUY/SELL panel or prove a complete trade interval.

`services/execution/_executor_submit.py:135` records shadow_would_be_fill with
configured fee/slippage assumptions and a local quote. It is a modeled order
record, not an arrival book, exchange fill or measured fee. The corresponding
`services/analytics/execution_cost_stack_report.py:242` examines those records;
its optional subsequent_price_path heuristic does not implement v3's same-arrival
paired depth walk, full residual fallback, or predeclared day-block endpoint.
Do not use its readiness threshold as E1's acceptance rule.

The existing defaults-25 pilot supplies hourly candles/metadata under its own
budget. It is neither an L2 arrival/trade collector nor an always-on E1 host proof.
Do not modify its job to quietly start another experiment.

## Exactly What Remains

1. Dated, product-applicable fee/rounding evidence for both products, without
   exposing account credentials. Preserve account-level evidence as provisional.
2. A reviewed numeric arrival freshness/alignment rule and treatment of clock
   uncertainty/missing source times. Do not invent a number from old diagnostics.
3. Explicit endpoint/trade-side/status/interval-coverage semantics and the same
   event exclusion mask for both execution methods. Resolve undefined resamples
   and inference readiness under E1's own design; ED-002's SB-1 work does not
   automatically validate E1's seven-day block method.
4. After contract review/adoption only, a narrowly scoped collector/normalizer
   and deterministic synthetic replay reusing the components above where valid.
   Host/schedule/real validation collection need separate bounded authorization.

No new observations, costs/fills, statistics or trial outcomes were computed.
No paid data, package install, account access, server/schedule, frozen criterion,
capital/risk or trading change. No profitability claim or numerical income
projection is supported by this readiness review. E1 can inform execution cost;
a favorable counterfactual cost comparison alone cannot establish strategy profit.

This is a bounded source/readiness reconciliation, not an exhaustive refresh of
the6326-line repository backlog or current remote operations.
