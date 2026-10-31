# Separate review: account-wide position-cap contract

2026-10-28. Reviewer active role GATE, separate agent
`01a11481-515d-7473-8ee3-7f6864c6d40b`.
Disposition: ACCEPTED_WITH_RISK for synthetic implementation only.
Production implementation, account completeness and deployment INCOMPLETE.

Reviewed contract SHA256:
`8bd9c90671481ad8a9105bca46af3725e4cc26749e31143110a3f4fd5124e59b`.
The reviewed file is preserved unchanged. The implementing/authoring parent is
recording a separately returned verdict, not independently approving itself.

## Returned Review

No material design blocker found. The reviewer reported reading all three
submitted documents and relevant excerpts from six source files, with no tests,
imports, private-state access, network operations or edits.

- Account scope preserves manual/bot holdings across pairs and required
  portfolios; inaccessible scope is unknown, not zero. Dedicated-account
  substitution is not authorized. Contract line12.
- Pending/fill overlap requires evidence-based deduplication; ambiguous submit,
  partial fills and incoherent observations retain exposure or refuse increases.
  Pending sells cannot prematurely free capacity. Contract line42.
- Durable shared atomic admission is required. The reviewer checked that sync
  and async submission semaphores are separate and the existing atomic queue
  claim is for daily counters, not asset exposure. place_order.py line708 and
  storage/live_intent_queue_sqlite.py line458.
- The cap adds no refusal solely for excess exposure or unavailable increase
  evidence on reducing sells; ownership, no-oversell and other gates remain.
  Contract line70.
- Explicit freshness/FX/order bounds remain required. External manual writers
  and price changes prevent an account-wide hard-cap guarantee. Contract lines66
  and110. Actual account completeness/production behavior remain UNVERIFIED.

This is a faithful recorded summary of the returned review, not a claim that
the parent independently reran the review or that a production fix exists.

## Exact Next Proof

Use real temporary local transactions and invented account data to demonstrate:

1. Mixed sync/async concurrent admission through one shared authority.
2. Cross-pair aggregation within verified account/base-asset identity.
3. Reservation retention through cancellation ambiguity, crashes and restart.
4. Coherent partial-fill reconciliation, with no premature capacity release
   from stale holdings snapshots.
5. Incomplete account/page evidence refuses increases, while the cap itself
   preserves reducing sells subject to existing independent gates.
6. Explicit synthetic freshness thresholds, not invented live settings.

The next implementation must be narrowly scoped and synthetic-only: no private
reads, account changes, live cap value changes, production wiring, migration,
service/scheduler changes, market-data run or trading. New financial/concurrency
code ends READY_FOR_INDEPENDENT_REVIEW; this design review cannot accept code
that has not been implemented or tested. Do not build a second execution router
or equate a model fixture with actual exchange/account coherence.
