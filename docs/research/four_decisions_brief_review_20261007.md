# Four-decisions brief review - 2026-10-07

Active role: AUDITOR. Disposition: INCOMPLETE as a current execution/decision packet; useful historical input. User requested review and advice, not configuration or campaign changes.

## Reviewed sources

Full attachment: /Users/baitus/.codex/attachments/63d23b9a-5def-4524-aa9b-fff08cdb3327/Pasted text.txt.
Current local market_quality_guard.py and strict template read in full. Current strategy YAML promotion section inspected. Remaining-89 review and the E03 addenda used to reconcile later evidence. No current account, running process or Hetzner inspection performed. Historic fee endpoint value remains historical, not refreshed account proof.

## Findings

1. The claim that none of the four decisions is a code task is too strong. Choosing a cohort and fee policy is an operator decision, but timestamp validation, exact fill-quote validation and unresolved execution/recovery findings require technical proof or correction. Approval of a policy does not establish its implementation.
2. The three trailing-stop trades should not establish performance of the declared no-trailing-stop strategy, conditional on the archived exit-rule evidence. Preserve them as diagnostic history. The YAML inspected still declares June 16 as cohort_start. A commit date is not a proven runtime transition. Do not choose a retroactive start from PR timing alone; establish the first verified matching runtime and cost/provenance version, or register a new prospective cohort when that version is operating. Do not erase old records, reset warmup or change thresholds to accelerate promotion.
3. The fee arithmetic is broadly coherent: 50 minus 7.5 is 42.5 bps per side; added modeled fees are 0.00425 times total entry-plus-exit turnover. An 85 bps round-trip comparison uses an approximately equal-notional reference; actual extra dollars depend on both fills. Re-query the exact account/product/venue tier before adopting 50 bps as current. Keep original accounting intact and label fee-restated historical results MODELLED. Five bps slippage remains an assumption, not measured execution.
4. Strict config alone is not a complete freshness contract. In the local guard, ts_ms=0 or missing skips the stale check even with block_when_unknown and require_bid_ask enabled. The template defines BTC/USDT's 20 bps override, not BTC/USD's; the latter uses the 50 bps general cap. Validate the exact campaign symbol and quote coverage. Entry restrictions must not be assumed safe for protective exits without checking callers. A quiet daily cycle with no order yields signal-time evidence only, not order-time proof.
5. The unreviewed-patch count/order is an October 4 snapshot, superseded by the full-content pass. Full reading is not blanket acceptance. Retain exact version-bound dispositions and unresolved findings rather than rerunning all old review work as if new. Current assembled-series accounting/recovery findings and the two static ambiguous-submit findings must remain visible before deployment.
6. The 16-month estimate is arithmetic from historical frequency, not a forecast or a profitability threshold. Five trades is a policy minimum, not statistical proof. Later E03 addenda retract charging the entire shared host to SMA200 and retract dismissing the host's evidence value: context collection is a separate job. Preserve research intelligence and evaluate marginal candidate cost separately from whole-platform infrastructure value.

## Recommendation

Create one versioned, read-only evidence checkpoint before changing the campaign: deployed/runtime identity, current account fee tier, exact symbol/currency and quote timestamp coverage, old-rule trade classification and the first demonstrably comparable cohort boundary. Record unknowns rather than guessing. Then propose the narrowly scoped cohort/fee/strict-entry configuration change with its effective timestamp and rollback; do not silently deploy the reviewed patch series or change live authorization.

No source, config, account, collector, push, merge or deployment changes. Tests not run; local source inspection supports the timestamp finding. Account rates, actual current gate count and host state remain UNVERIFIED. Coinbase's official Advanced-fees guidance says fees vary by product, tier and maker/taker status and directs customers to the account fee page: https://help.coinbase.com/en-gb/coinbase/trading-and-funding/advanced-trade/advanced-trade-fees.
