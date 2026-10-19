# Shadow would-be-fill recorder (backlog item 3): slippage was not a measurement

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0051 (commit f57547b6, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev62.zip`,
folder 59. Zip SHA-256:
0da40f3169a8dfc82897fb44a5442ceb2e993a1bc23ef7d31d590bf4ca88c27e

## What holds

Observe-only mode records one would-be fill per pending intent, idempotently,
without creating the exchange client or any execution-store fill, and leaves
the intent pending.

## Findings

1. P2, paper. Every fill recorded slippage 0: the engine compared the fill
   price with itself. In this checkout all 16 candidate fill records (and the
   one `ema_cross_default` record) have `slippage_pct: 0.0`, although each was
   filled 5 bps off the mid. The slippage check passes trivially, the warn
   (1.5x) and halt (3x) multipliers cannot trigger, and replacing the 0.10%
   baseline "after first 50 fills", as the config says, would replace it with
   zero.
2. P2, shadow. A would-be fill's `slippage_pct` is the modelled assumption
   (default 5 bps) applied to the mid, so it always equals the assumption. The
   recorder checks neither the quote's age nor the intent's.

## Correction in 0051

- Paper: slippage is measured against the intent's `reference_price` or, for a
  limit order, its limit; None when there is neither. New fields
  `slippage_reference`, `slippage_reference_price`, `slippage_bps_adverse`
  (signed). It includes price movement between decision and fill.
- Shadow: the record carries `slippage_basis: assumed_model`, the measured
  `half_spread_bps`, and `quote_age_s`.

12 new cases, 11 fail on the previous code. Full suite: 4648 passed, 33
skipped, 19 failed (the same 19 as master).

## Not changed

- The 16 existing records keep their zeros; treat slippage in fills written
  before this patch as not measured.
- The shadow recorder still records against a quote or intent of any age.
- The shadow fee default is 10 bps; the recorded taker rate is 50.
- Book depth is not captured, so the cost of size is not measured anywhere.
