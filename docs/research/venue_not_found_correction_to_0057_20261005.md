# Correction to patch 0057: explicit venue "order not found" - 2026-10-05

Reviewer: Claude. Scope: `services/execution/live_reconciler.py`. Result: patch 0074
(`1e1460c1`), bundle rev85 folder 82. READY_FOR_INDEPENDENT_REVIEW, LIVE-PATH. Not pushed.

**Patch 0057 must not be applied without 0074. Review them together.**

## The documented rule (`docs/AUTHORITY_MATRIX.md`, Orders)

- Exchange says not found, order younger than the stale threshold: leave `submitted`, retry.
- Exchange says not found, order older: exchange wins, `error: stale_order_not_found`.

Launch drill 3.4 checks it with a fake exchange order id.

## Finding (P2, introduced by my patch 0057)

The venue library says "not found" by raising `OrderNotFound`. 0057 made every exception from
a venue lookup keep the order `submitted` and looked up again. That is right for a failure
to ask (network, rate limit, authentication). It also caught the explicit answer: an intent
whose venue id the exchange does not know stayed `submitted` with
`stale_order_fetch_error:OrderNotFound` for ever, and drill 3.4 could not pass. 0057's tests
used `ConnectionError` only, which is why they did not catch it.

## Patch 0074

- `OrderNotFound` (or a subclass) past the stale age closes the intent as
  `stale_order_not_found`; before it the intent stays `submitted`.
- Every other lookup error still keeps the order tracked.

9 tests, 2 fail on the series before this patch. Full suite: 4901 passed, 33 skipped, 0 failed.

## Not changed

A single explicit not-found past the stale age closes the intent. That is the documented
rule; an unknown submit, by contrast, needs three clean not-founds over 15 minutes (0073).
