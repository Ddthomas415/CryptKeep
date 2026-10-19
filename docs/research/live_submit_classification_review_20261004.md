# Order retry classification (live-money backlog item 3): independent review

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0045 (commit b2b3a48f, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev56.zip`,
folder 53. Zip SHA-256:
b661466c006eb960bba9267aee29d4ea64f66e3efb676256f2a1745e746edccb

## What holds

`retry_policy.is_retryable_exception` classifies by type and never reads
message text.

## Findings

1. That function's only users, `order_router.place_order_idempotent` and
   `fill_confirmation`, are imported by no production module. The 2026-07-06
   slice hardened code no entry point reaches.
2. P1 for live, latent now. The reachable live submit,
   `ExchangeClient.submit_order` (used by `live_executor.submit_pending_live`),
   decided "ambiguous" by matching six exception type names. With the real
   client and dedupe store and a venue that accepts the order and then fails
   the response with `ccxt.ExchangeError`, `BadResponse`, `NullResponse`,
   `OnMaintenance`, `OperationFailed` or `ConnectionResetError`, the dedupe row
   was marked `error`, the next submit was allowed, and the venue received a
   second order.

This checkout's effective config has all three live switches false.

## Correction in 0045

- Submit errors are classified by type: any ccxt error that is not a
  definitive rejection is ambiguous, as are builtin connection and timeout
  errors. Ambiguous marks the dedupe row `unknown`, which blocks a resubmit.
- Correction to patch 0039: the intent TTL no longer cancels an intent whose
  dedupe row says submitted, acknowledged or unknown, has a remote order id,
  or cannot be read. 0039 as first written could cancel locally an intent
  whose order might be live at the venue. Review 0039 and 0045 together.

17 new cases (6 fail on the previous code) plus 8 added TTL cases (5 fail).
Full suite: 4592 passed, 33 skipped, 19 failed (the same 19 as master).

## Not changed, and a decision for the operator

The executor path cannot resolve an `unknown` submit by itself: its reconcile
step skips an intent with no remote order id, and its client-order-id lookup
is called on the raw ccxt object, which lacks that method, so it always returns
`inconclusive`. An unknown intent stays blocked until resolved by hand. The
other live path (`live_intent_consumer` with `live_reconciler`) has a
`submit_unknown` lane. Decide which live path is intended; if it is the
executor, it needs an unknown-resolution step before live.
