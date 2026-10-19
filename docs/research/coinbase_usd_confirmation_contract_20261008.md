# Separate Coinbase USD confirmation draft

User approved the all-five USD quote change after the USDT warmup failed
continuity for ADA and XRP. The USDT plan, archive and failed preflight are
preserved. The new plan is `research/coinbase_confirmation_usd_v1/plan.json`.

BTC, ETH, SOL, ADA and XRP use exact Coinbase USD products and a separate
archive. USD results must not be relabelled as USDT results. Strategies,
source snapshot, dates, cash, entry size, fee evidence and uncertainty rules
remain unchanged. The runner accepts only either complete homogeneous basket,
with the declared quote matching the products; mixed baskets are rejected.

This is DRAFT_NOT_ACTIVATED. No registration, signal scoring, orders, campaign
changes or new background collector are authorized by this implementation.
Full 300-hour warmup cannot be verified until the last warmup candle closes
at 2026-10-10 00:00 UTC. Partial public-data coverage is not activation proof.

Targeted verification: 41 tests passed, including the USD contract and refusal
of mixed, partial and misdeclared quote baskets. Exact symbol routing was
checked locally for all five USD symbols. Financial research implementation:
READY_FOR_INDEPENDENT_REVIEW at implementation handoff. Separate GATE then
accepted the contract/runner change with risk and independently reran 41 tests.

## Bounded public-data preflight

All five exact USD symbols have 275 valid contiguous hourly candles from
2026-09-27 12:00 UTC through 2026-10-08 23:00 UTC exclusive. Saved backfill
receipts and `warmup_preflight_20261008.json` reside alongside the USD plan.
Strict archive replay checks numeric OHLCV validity and the complete hour grid.
This fixed historical cutoff is not a claim of current freshness. The remaining
25 hours were outside this preflight; full 300-hour warmup is still unverified.
No registration, freeze or signal scoring was performed.
