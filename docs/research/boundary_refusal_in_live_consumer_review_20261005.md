# Boundary refusals in the canonical live consumer - 2026-10-05

Reviewer: Claude. Scope: `services/execution/live_intent_consumer.py`,
`storage/live_intent_queue_sqlite.py`. Result: patch 0071 (`bc325a33`), bundle rev82
folder 79. READY_FOR_INDEPENDENT_REVIEW, LIVE-PATH. Not pushed.

Correction to an earlier note: I filed this as "a transient gate block becomes terminal
rejected". That describes the consumer's own pre-checks. A refusal raised by the order
boundary took the generic exception path.

## Findings (P2 for live)

Tests use the real intent queue, live trading store and dedupe store.

1. `RuntimeError("CBP_ORDER_BLOCKED:...")` (raised before any venue call) was handled as an
   unknown submit: a second venue lookup, then `submit_unknown` for the reconciler to chase.
2. The daily trade/notional claim taken before the submit was never given back. With
   `max_trades_per_day = 2`, two refused buys left the count at 2 and the sell that followed
   was rejected as `risk:max_trades_per_day`. Refused entries could block an exit.
3. The same for an order the router declined.

## Patch 0071

- Boundary refusals are recorded as `rejected` (`boundary:<text>`), no further venue lookup.
- Their claim, and a router rejection's, is given back (never below zero).
- Every other submit error is still `submit_unknown` and keeps its claim.

10 tests, 5 fail on the previous code. Full suite: 4876 passed, 33 skipped, 0 failed.

## Not fixed

- A refused intent is terminal; it is not retried later.
- (Corrected, see below.) I listed market-rule failures here as lacking the
  `CBP_ORDER_BLOCKED:` prefix. They carry it, so 0071 already covers them.
- The boundary's own daily limits (`CBP_MAX_*`) are separate counters, untouched.

## Follow-up: patch 0072 (`da740471`), bundle rev83 folder 80

Correction: `place_order` re-raises market-rule and prerequisite failures as
`CBP_ORDER_BLOCKED:market_rules_invalid:` / `market_rules_prereq_failed:`. Every refusal it
raises before the venue call carries the prefix.

The remaining pre-submit failure without the prefix was the exchange adapter failing to
build (missing credentials, client construction). Test with the real stores, three queued
intents, no credentials, `max_trades_per_day = 2`, previous code: all three became
`submit_unknown` and kept their claims; the third was rejected as `risk:max_trades_per_day`;
`last_error` held the raw exception text. No adapter existed, so nothing could have been sent.

0072 records such an intent as `rejected` with `adapter_unavailable:<exception type>` and
gives its claim back. Two tests added (12 in all), both fail on the previous code. Full
suite: 4878 passed, 33 skipped, 0 failed.

Not fixed: the intent is terminal (credentials fixed later do not revive it); other submit
errors still store the raw exception text in `last_error`.
