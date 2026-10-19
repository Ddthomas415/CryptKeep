# Giving up an unknown submit: failed lookup vs not found - 2026-10-05

Reviewer: Claude. Scope: `services/execution/live_exchange_adapter.py`,
`services/execution/live_reconciler.py`. Result: patch 0073 (`dd972ca6`), bundle rev84
folder 81. READY_FOR_INDEPENDENT_REVIEW, LIVE-PATH (restrictive only). Not pushed.

## Finding (P1 for live)

The reconciler closes a `submit_unknown` intent as `error` after three not-found observations
over at least 15 minutes. Its comment says only clean not-found answers are counted because
lookup exceptions propagate. They do not: `find_order_by_client_oid` wraps the open-order and
the closed-order lookup each in `except Exception: pass` and returns None.

Tests (the adapter's real lookup code over a stand-in venue client, real intent queue and
trading store, the reconciler's real lane), previous code:

| Venue behaviour | Result |
|---|---|
| every lookup raises `ConnectionError` | closed as `submit_unknown_not_found_terminal` on the 4th pass, 20 minutes in |
| only the closed-order lookup fails | same (a filled order is visible only there) |
| venue client has no closed-order lookup | same |

An order placed just before an outage would be dropped from tracking and its fill never
accounted.

## Patch 0073

- Adapter: `find_order_by_client_oid_checked` returns `(order, conclusive, detail)`. Absence
  is conclusive only when both lookups answered.
- Reconciler: an inconclusive pass is logged, does not count toward the three observations
  and leaves the intent in `submit_unknown`.

14 tests, 10 fail on the previous code. Full suite: 4892 passed, 33 skipped, 0 failed.

## Not fixed

- Thresholds unchanged. A clean not-found still closes the intent, so a venue that lists
  only recent closed orders can still hide an old fill.
- An intent on a venue that never proves absence stays `submit_unknown` until you resolve it.
- `stale_order_not_found` for an order that has a venue id.
